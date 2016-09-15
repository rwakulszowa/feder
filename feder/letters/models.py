from __future__ import print_function

import os
import uuid
from textwrap import TextWrapper

import claw
from atom.models import AttachmentBase
from claw import quotations
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db import models
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django_mailbox.models import Message
from django_mailbox.signals import message_received
from model_utils.models import TimeStampedModel

from feder.cases.models import Case
from feder.institutions.models import Institution

from .utils import email_wrapper

claw.init()


class LetterQuerySet(models.QuerySet):
    def attachment_count(self):
        return self.annotate(attachment_count=models.Count('attachment'))

    def for_milestone(self):
        return (self.prefetch_related('attachment_set').
                select_related('author_user', 'author_institution'))

    def is_outgoing(self):
        return self.filter(author_user__isnull=False)

    def is_incoming(self):
        return self.filter(author_user__isnull=True)


@python_2_unicode_compatible
class Letter(TimeStampedModel):
    case = models.ForeignKey(Case, verbose_name=_("Case"))
    author_user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("Author (if user)"),
                                    null=True, blank=True)
    author_institution = models.ForeignKey(Institution, verbose_name=_("Author (if institution)"),
                                           null=True, blank=True)
    title = models.CharField(verbose_name=_("Title"), max_length=50)
    body = models.TextField(verbose_name=_("Text"))
    quote = models.TextField(verbose_name=_("Quote"), blank=True)
    email = models.EmailField(verbose_name=_("E-mail"), max_length=50, blank=True)
    eml = models.FileField(upload_to="messages/%Y/%m/%d",
                           verbose_name=_("File"),
                           null=True)
    message = models.ForeignKey(Message,
                                null=True,
                                verbose_name=_("Message"),
                                help_text=_("Message registerd by django-mailbox"))
    objects = LetterQuerySet.as_manager()

    class Meta:
        verbose_name = _("Letter")
        verbose_name_plural = _("Letters")
        ordering = ['created', ]
        permissions = (
            ("can_filter_eml", _("Can filter eml")),
        )

    @property
    def is_draft(self):
        return self.is_outgoing and not bool(self.eml)

    @property
    def is_incoming(self):
        return not bool(self.author_user_id)

    @property
    def is_outgoing(self):
        return bool(self.author_user_id)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('letters:details', kwargs={'pk': self.pk})

    @property
    def author(self):
        return self.author_user if self.author_user_id else self.author_institution

    @author.setter
    def author(self, value):
        if isinstance(value, Institution):
            self.author_user = None
            self.author_institution = value
        elif isinstance(value, get_user_model()):
            self.author_institution = None
            self.author_user = value
        else:
            raise ValueError("Only User and Institution is allowed for attribute author")

    @classmethod
    def send_new_case(cls, user, monitoring, institution, text, postfix=''):
        case = Case(user=user,
                    name=monitoring.name + postfix,
                    monitoring=monitoring,
                    institution=institution)
        case.save()
        letter = cls(author_user=user, case=case, title=monitoring.name, body=text)
        letter.send(commit=True, only=False)
        return letter

    def email_body(self):
        body = self.body.replace('{{EMAIL}}', self.case.email)
        return u"{0}\n{1}".format(body, email_wrapper(self.quote))

    def _construct_message(self):
        headers = {'Return-Receipt-To': self.case.email,
                   'Disposition-Notification-To': self.case.email}
        return EmailMessage(subject=self.case.monitoring,
                            from_email=self.case.email,
                            reply_to=[self.case.email],
                            to=[self.case.institution.accurate_email.email],
                            body=self.email_body(),
                            headers=headers)

    def send(self, commit=True, only=False):
        message = self._construct_message()
        text = message.message().as_bytes()
        self.email = self.case.institution.accurate_email.email
        self.eml.save('%s.eml' % uuid.uuid4(), ContentFile(text), save=False)
        if commit:
            self.save(update_fields=['eml', 'email'] if only else None)
        return message.send()

    @classmethod
    def process_incoming(cls, case, message):
        # Extract text and quote
        if message.text:
            text = quotations.extract_from(message.text, 'text/plain')
            quote = message.text.replace(text, '')
        else:
            text = quotations.extract_from(message.html, 'text/html')
            quote = message.text.replace(text, '')

        # Create Letter
        obj = cls.objects.create(author_institution=case.institution,
                                 email=message.from_address[0],
                                 case=case,
                                 title=message.subject,
                                 body=text,
                                 quote=quote,
                                 eml=File(message.eml, message.eml.name),
                                 message=message)
        attachments = []
        # Append attachments
        for attachment in message.attachments.all():
            name = attachment.get_filename() or 'Unknown.bin'
            if len(name) > 70:
                name, ext = os.path.splitext(name)
                ext = ext[:70]
                name = name[:70 - len(ext)] + ext
            file_obj = File(attachment.document, name)
            attachments.append(Attachment(letter=obj, attachment=file_obj))
        Attachment.objects.bulk_create(attachments)
        return obj, attachments


class Attachment(AttachmentBase):
    letter = models.ForeignKey(Letter)


@receiver(message_received)
def mail_process(sender, message, **args):
    try:
        case = Case.objects.by_msg(message).get()
    except Case.DoesNotExist:
        print("Message #{pk} skip, due not recognized address {to}".
              format(pk=message.pk, to=message.to_addresses))
        return
    letter, attachments = Letter.process_incoming(case, message)
    print("Message #{message} registered in case #{case} as letter #{letter}".
          format(message=message.pk, case=case.pk, letter=letter.pk))
