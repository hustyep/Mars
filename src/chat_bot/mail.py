from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from src.common import config


def sendText(message: str, Subject: str):
    msg = MIMEText(message, 'plain', 'utf-8')
    msg["Subject"] = Subject
    msg["from"] = 'maple_bot'
    msg["to"] = config.mail_to_addrs
    
    with SMTP_SSL(host="smtp.163.com", port=465) as smtp:
    # 登录发邮件服务器
        smtp.login(user=config.mail_user, password=config.mail_password)
        # 实际发送、接收邮件配置
        smtp.sendmail(from_addr=config.mail_user, to_addrs=config.mail_to_addrs.split(
            ','), msg=msg.as_string())
    
def sendImage(message: str, Subject: str, imagePath: str):
    '''
    :param message: str 邮件内容
    :param Subject: str 邮件主题描述
    :param sender_show: str 发件人显示，不起实际作用如："xxx"
    :param recipient_show: str 收件人显示，不起实际作用 多个收件人用','隔开如："xxx,xxxx"
    :param to_addrs: str 实际收件人
    :param cc_show: str 抄送人显示，不起实际作用，多个抄送人用','隔开如："xxx,xxxx"
    '''

    # 邮件内容
    msg = MIMEMultipart('related')  # 邮件类型，如果要加图片等附件，就得是这个

    # 邮件主题描述
    msg["Subject"] = Subject
    # 发件人显示，不起实际作用
    msg["from"] = 'maple_bot'
    # 收件人显示，不起实际作用
    msg["to"] = config.mail_to_addrs
    # 抄送人显示，不起实际作用
    # msg["Cc"] = cc_show

    # 以下为邮件正文内容，含有一个居中的标题和一张图片
    content = MIMEText(
        '<html><div id="string">' + message + '<div></head><body><img src="cid:image1" alt="image1"></body></html>', 'html', 'utf-8')
    # 如果有编码格式问题导致乱码，可以进行格式转换：
    # content = content.decode('utf-8').encode('gbk')
    msg.attach(content)

    # 上面加的图片src必须是cid:xxx的形式，xxx就是下面添加图片时设置的图片id
    # 添加图片附件
    fp = open(imagePath, 'rb')
    msgImage = MIMEImage(fp.read())
    fp.close()
    msgImage.add_header('Content-ID', 'image1')  # 这个id用于上面html获取图片
    msg.attach(msgImage)

    with SMTP_SSL(host="smtp.163.com", port=465) as smtp:
        # 登录发邮件服务器
        smtp.login(user=config.mail_user, password=config.mail_password)
        # 实际发送、接收邮件配置
        smtp.sendmail(from_addr=config.mail_user, to_addrs=config.mail_to_addrs.split(
            ','), msg=msg.as_string())

if __name__ == "__main__":
    message = 'Python 测试邮件...'
    Subject = '主题测试1'

    # sendImage(message, Subject, "assets/icon.png")
    sendText(message, Subject)

