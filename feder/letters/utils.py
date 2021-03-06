from textwrap import TextWrapper

BODY_FOOTER_SEPERATOR = "\n\n--\n"


def email_wrapper(text):
    wrapper = TextWrapper()
    wrapper.subsequent_indent = "> "
    wrapper.initial_indent = "> "
    return "\n".join(wrapper.wrap(text))


def normalize_msg_id(msg_id):
    if msg_id[0] == "<":
        msg_id = msg_id[1:]
    if msg_id[-1] == ">":
        msg_id = msg_id[:-1]
    return msg_id


def is_spam_check(email_object):
    return email_object["X-Spam-Flag"] == "YES"


def get_body_with_footer(body, footer):
    if footer.strip():
        return "{}{}{}".format(body, BODY_FOOTER_SEPERATOR, footer)
    return body
