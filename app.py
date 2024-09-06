# Libraries
from flask import Flask, render_template, request
import re
import random
import os
import subprocess

# Functions
# function to check if an email is valid
def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

# function to create motifscope command
def createMotifscopeCommand(random_number):
    # define input reads
    input_reads = 'runs/run_%s/run_%s_input.txt' %(random_number, random_number)
    output_folder = 'runs/run_%s' %(random_number)
    command = 'motifscope --sequence-type assembly -i %s -o %s' %(input_reads, output_folder)
    return command

# Create a Flask app instance
app = Flask(__name__)

# Annotation section
@app.route('/', methods=["GET", "POST"])
@app.route('/index/', methods=["GET", "POST"])
def index():
    # email
    email = request.form.get('email', '')
    email = email.replace(' ', '').rstrip()
    # check if email is valid
    emailResponse = is_valid_email(email)
    # modify the message linked to submission
    messageSubmission = ''
    # generte random number
    random_number = random.randint(0, 1000000)
    if request.method == "POST":
        # Read inputs
        textarea_input = request.form.get('SNPlist', '')
        uploaded_file = request.files.get('fasta_file')
        # parse other inputs here
        # ...
        # update message
        if emailResponse == True:
            messageSubmission = 'Your job has been submitted! Check your email shortly.'
            # create directory with run information
            os.system('mkdir runs/run_%s' %(random_number))
            if textarea_input != '':
                # write this file as it is the input for motifscope
                fout = open('runs/run_%s/run_%s_input.txt' %(random_number, random_number), 'w')
                fout.write(textarea_input)
                fout.close()
            elif uploaded_file and uploaded_file.filename != '':
                input_fasta = uploaded_file.read().decode('utf-8')
                fout = open('runs/run_%s/run_%s_input.txt' %(random_number, random_number), 'w')
                fout.write(input_fasta)
                fout.close()
            # run the script here
            #command = 'sh run_docker_webserver.sh runs/run_%s/run_%s_input.txt runs/run_%s' %(random_number, random_number, random_number)
            command = createMotifscopeCommand(random_number)
            print(command)
            command_run = subprocess.Popen(command, shell=True)
        else:
            messageSubmission = 'Email is not correct. Please check!'
    return render_template('index.html', validEmail=emailResponse, messageSubmission=messageSubmission) 

# Run the app
if __name__ == '__main__':
    app.run(debug=True)