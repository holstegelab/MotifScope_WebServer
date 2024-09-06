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
    # define input reads
    input_reads = 'runs/run_%s/run_%s_input.txt' %(random_number, random_number)
    output_folder = 'runs/run_%s/run_%s_output' %(random_number, random_number)
    output_compressed = 'runs/run_%s.tar.gz' %(random_number)
    log_file = 'runs/run_%s/run_%s_output.log' %(random_number, random_number)
    command = 'motifscope --sequence-type reads -i %s -o %s >> %s' %(input_reads, output_folder, log_file)
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
        if os.path.exists('runs/run_%s' %(run_id)):
            messageError = False
            messageToUser = 'Valid Run ID. Download will start soon'
            # compress folder and remove original folder
            os.system('tar -cvf runs/run_%s.tar.gz runs/run_%s && rm -rf runs/run_%s' % (run_id, run_id, run_id))
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
    # read inputs
    textarea_input = request.form.get('SNPlist', '')
    uploaded_file = request.files.get('fasta_file')
    # parse other inputs here
    # ...
    if (textarea_input != '') or (uploaded_file and uploaded_file.filename != ''):
        # if there was an input of some sort, create random number and output folder
        # generate random number
        random_number = random.randint(0, 1000000)
        # create output directory
        os.system('mkdir runs/run_%s' %(random_number))
        # message to the user with the run id
        messageSubmission = 'Your job has been submitted with ID: %s. Check Download page shortly to get your results' %(random_number)
        # then check what input that was
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
        command = createMotifscopeCommand(random_number)
        command_run = subprocess.Popen(command, shell=True)
    else:
        messageSubmission = ''
    return render_template('index.html', messageSubmission=messageSubmission) 

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