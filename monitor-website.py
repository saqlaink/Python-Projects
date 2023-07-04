import requests
import smtplib
import os
import paramiko
import linode_api4
import time
import schedule

EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
LINODE_TOKEN = os.environ.get('LINODE_TOKEN')

def send_notification(email_msg):
  with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
    smtp.starttls()
    smtp.ehlo()
    smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD) #https: //myaccount.google.com/apppasswords
    msg = f'Subject: SITE DOWN\n{email_msg}'
    smtp.sendmail(EMAIL_ADDRESS,EMAIL_ADDRESS, msg)

def restart_container():
    print('Restarting the Application.....')
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname='139.162.130.236',username='root',key_filename='/Users/saqlain/.ssh/id_rsa')
    stdin, stdout,stderr = ssh.exec_command('docker start c3e706bc905e')
    print(stdin.readline())
    ssh.close()

def restart_server_and_app():
   #restart linode server
    print("Rebooting the server.....")
    client = linode_api4.LinodeClient(LINODE_TOKEN)
    nginx_server = client.load(linode_api4.Instance, 24920590)
    nginx_server.reboot()

    #restart the application
    while True:
        nginx_server = client.load(linode_api4.Instance, 24920590)
        if nginx_server.status == 'running':
            time.sleep(5)
            restart_container()
            break

def monitor_application():
  try:
    response = requests.get('http://li1388-236.members.linode.com:8080/')
    if response.status_code == 200:
        print('Application is running successfully!')
    else:
        print('Application Down! Fix it')
        #send email to me
        msg = f"Application returned {response.status_code}. Fix the issue!"
        send_notification(msg)

        #restart the app
        restart_container()
  except Exception as ex:
      print('Err')
      message = "Application not accessible at all. Fix the issue!"
      send_notification(message)
      restart_server_and_app()

schedule.every(5).minutes.do(monitor_application)

while True:
   schedule.run_pending()
