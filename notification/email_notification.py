#coding:utf-8
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import time

import sys
sys.path.append("..")
import config.notification_account as notification_account



class EmailNotification:
	# 通过邮件发送提醒
	
	def __init__(self):
		# 设置发送邮件的参数
		# 设置服务器,第三方 SMTP 服务
		self.email_host = notification_account.email_host
		# 用户名
		self.email_user = notification_account.email_user
		# 获取授权码，不是密码
		self.email_pass = notification_account.email_pass
		# 发件人账号
		self.email_sender = notification_account.email_sender
		# 接收邮件
		self.email_receivers = notification_account.email_receivers
		# 获取当前时间
		self.today= time.strftime("%Y-%m-%d", time.localtime())
		# 设置邮件主题
		self.subject = self.today+' 基金行情分析'
	
	'''
	def get_index_real_time_pe(self,index_code):
		# 获取指数的实时市盈率
		# index_code: 指数代码
		# 返回 指数的实时市盈率
		
		index_real_time_pe_ttm = strategy.calculate_index_pe.CalculateIndexPE().calculate_real_time_index_pe_multiple_threads(index_code)
	
		return index_real_time_pe_ttm
	'''
	
	def send_customized_content(self,send_content):
		# 自定义邮件的内容
		
		# MIMEText 类来实现支持HTML格式的邮件，支持所有HTML格式的元素，包括表格，图片，动画，css样式，表单
		# 第一个参数为邮件内容,第二个设置文本格式，第三个设置编码
		message = MIMEText(send_content, 'plain', 'utf-8')  
		# 发件人
		message['From'] = self.email_sender  
		# 收件人
		message['To'] = ",".join(self.email_receivers)
		# 主题
		message['Subject'] = Header(self.subject, 'utf-8')
	
		try:
			# 创建实例
			smtpObj = smtplib.SMTP()
			# 连接服务器，25 为 SMTP 端口号
			smtpObj.connect(self.email_host, 25)  
			# 登录账号
			smtpObj.login(self.email_user, self.email_pass)
			# 发送邮件
			smtpObj.sendmail(self.email_sender, self.email_receivers, message.as_string())
			print("邮件发送成功")
		except smtplib.SMTPException as e:
			print(e)
			print("Error: 无法发送邮件")
	
	
if __name__ == '__main__':
	time_start = time.time()
	go = EmailNotification()
	#real_time_pe = go.get_index_real_time_pe('399997')
	send_content = 'hello ccx, 2021-01-17  '
	go.send_customized_content(send_content)
	time_end = time.time()
	print(time_end-time_start)
	