# Libraries
from flask import Flask, render_template, request, send_file
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
    # create output directory
    os.system('mkdir runs/run_%s' %(random_number))
    # define input reads
    input_reads = 'runs/run_%s/run_%s_input.txt' %(random_number, random_number)
    output_folder = 'runs/run_%s/run_%s_output' %(random_number, random_number)
    output_compressed = 'runs/run_%s.tar.gz' %(random_number)
    log_file = 'runs/run_%s/run_%s_output.log' %(random_number, random_number)
    command = 'motifscope --sequence-type reads -i %s -o %s >> %s; tar -cvf %s runs/run_%s; rm -rf runs/run_%s' %(input_reads, output_folder, log_file, output_compressed, random_number, random_number)
    effective_command = 'echo %s > %s' %(command, log_file)
    save_command_line =  subprocess.Popen(effective_command, shell=True)
    return command

# function to check whether the run_id is correct
def check_runID(run_id):
    run_id = run_id.replace(' ', '')
    if run_id == '':
        messageError = True
        messageToUser = 'Please insert a valid Run ID'
    else:
        # check whether the file exists
        if os.path.exists('runs/run_%s.tar.gz' %(run_id)):
            messageError = False
            messageToUser = 'Valid Run ID. Download will start soon'
        else:
            messageError = True
            messageToUser = 'Not valid Run ID. Try again.'
    return messageError, messageToUser

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
    #emailResponse = is_valid_email(email)
    emailResponse = True
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
            messageSubmission = 'Your job has been submitted with ID: %s. Check Download page shortly to get your results' %(random_number)
            # create directory with run information
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
            command_run = subprocess.Popen(command, shell=True)
        else:
            messageSubmission = 'Email is not correct. Please check!'
    return render_template('index.html', validEmail=emailResponse, messageSubmission=messageSubmission) 

# Download tab
@app.route('/download/', methods=["GET", "POST"])
def download():
    run_id = None
    messageError = None
    messageToUser = None
    if request.method == 'POST':
        run_id = request.form["run_id"]
        messageError, messageToUser = check_runID(run_id)
    return render_template('download.html', run_id=run_id, messageError=messageError, messageToUser=messageToUser)

# Actual download button for the annotation results
@app.route('/downloadResults/<run_id>', methods=["GET"])
def download_results(run_id):
    # check here the run ID
    filename = f"run_{run_id}.tar.gz"
    filepath = os.path.join("runs", filename)
    return send_file(filepath, as_attachment=True, download_name=filename)

@app.route('/about/', methods=["GET"])
def about():
    return render_template("about.html")

# Run the app
if __name__ == '__main__':
    app.run(debug=True)