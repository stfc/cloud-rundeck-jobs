import os
from st2common.runners.base_action import Action
from smtplib import SMTP_SSL
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate


class Send_Email(Action):
    def run(self, **kwargs):
        """
        function that is run by stackstorm when an action is invoked
        :param kwargs: arguments for openstack actions
        :return: (Status (Bool), Output <*>): tuple of action status (succeeded(T)/failed(F)) and the output
        """
        if "body" in kwargs.keys() and kwargs["body"]:
            return self.send_email(**kwargs)
        return None

    def send_email(self, **kwargs):
        """
        Send email
        :param kwargs: email_to (String): Recipient Email,
        email_from (String): Sender Email, subject (String): Email Subject,
        header (String): filepath to header file,
        footer (String): filepath to footer file,
        body (String): body of email,
        attachment (List): list of attachment filepaths,
        smtp_account (String): email config to use,
        admin_override (Boolean): send all emails to admin email - testing purposes,
        admin_override_email (String): send to this email if admin_override enabled
        :return:
        """
        print("TO SEND")
        print("TO: {0}".format(kwargs["email_to"]))
        print("FROM: {0}".format(kwargs["email_from"]))
        print("SUBJECT: {0}".format(kwargs["subject"]))
        print("BODY: {0}\n{1}\n{2}".format(kwargs["header"], kwargs["body"], kwargs["footer"]))
        print("ATTACHMENT FILEPATHS: {0}".format(kwargs["attachment_filepaths"]))

        accounts = self.config.get('smtp_accounts', None)
        if not accounts:
            raise ValueError("'smtp_account' config value is required to send email, config={0}".format(self.config))
        try:
            kv = {a["name"]:a for a in accounts}
            account_data = kv[kwargs["smtp_account"]]
        except KeyError:
            raise KeyError("The account {0} does not appear in the configuration".format(kwargs["smtp_account"]))

        msg = MIMEMultipart()
        msg["Subject"] = Header(kwargs["subject"], 'utf-8')
        msg["From"] = kwargs["email_from"]

        if not kwargs["admin_override"]:
            msg["To"] = ", ".format(kwargs["email_to"])
        else:
            msg["To"] = ", ".format(kwargs["admin_override_email"])
        msg["Date"] = formatdate(localtime=True)

        if "header" in kwargs.keys() and os.path.exists(kwargs["header"]):
            with open(kwargs["header"], 'r', encoding='utf-8') as header_file:
                header = header_file.read()
        if "footer" in kwargs.keys() and os.path.exists(kwargs["footer"]):
            with open(kwargs["footer"], 'r', encoding='utf-8') as footer_file:
                footer = footer_file.read()

        if kwargs["send_as_html"]:
            msg.attach(MIMEText("""\
            <html>
                <head></head>
                <body>
                    {0}
                    {1}
                    {2}
                </body>
            </html>
            """.format(header, kwargs["body"], footer), "html"))
        else:
            msg.attach(MIMEText("{0}\n{1}\n{2}".format(header, kwargs["body"], footer), "plain", "utf-8"))

        if kwargs["email_cc"]:
            msg["Cc"] = ", ".join(kwargs["email_cc"])
        attachments = kwargs["attachment_filepaths"] or tuple()
        for filepath in attachments:
            filename = os.path.basename(filepath)
            with open(filepath, 'rb') as f:
                part = MIMEApplication(f.read(), Name=filename)
            part["Content-Disposition"] = "attachment; filename={0}".format(filename)
            msg.attach(part)

        smtp = SMTP_SSL(account_data["server"], str(account_data["port"]), timeout=60)
        smtp.ehlo()

        if account_data.get('secure', True):
            smtp.starttls()
        if account_data.get('smtp_auth', True):
            smtp.login(account_data['username'], account_data['password'])

        if not kwargs["admin_override"]:
            return (False, "No admin override set - disabled for testing purposes")
            # email_to = (kwargs["email_to"] + kwargs["email_cc"]) if kwargs["email_cc"] else kwargs["email_to"]
        else:
            email_to = kwargs["admin_override_email"]
        smtp.sendmail(kwargs["email_from"], email_to, msg.as_string())
        smtp.quit()
        return



