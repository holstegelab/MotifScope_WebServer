# Libraries
from flask import Flask, render_template, request, send_file
import re
import random
import os
import subprocess
import smtplib
from email.mime.text import MIMEText

# Functions
# function to check if an email is valid
def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

# function to create motifscope command
def createMotifscopeCommand(random_number, sequence_type, population, min_k, max_k, figure, figure_format, msa, reverse, motif_guided, email):
    # define input reads
    input_reads = 'runs/run_%s/run_%s_input.fa' %(random_number, random_number)
    population = 'runs/run_%s/run_%s_population.txt' %(random_number, random_number)
    ref_motifs = 'runs/run_%s/run_%s_motifs.txt' %(random_number, random_number)
    output_folder = 'runs/run_%s/run_%s_output' %(random_number, random_number)
    output_compressed = 'runs/run_%s.tar.gz' %(random_number)
    log_file = 'runs/run_%s/run_%s_output.log' %(random_number, random_number)
    command = 'motifscope --sequence-type %s -i %s -mink %s -maxk %s -o %s -p %s -figure %s -format %s -r 1 -msa %s -reverse %s -g %s -motif %s >> %s; echo "process is done"; python3 send_email.py %s %s' %(sequence_type, input_reads, str(min_k), str(max_k), output_folder, population, figure, figure_format, msa, reverse, motif_guided, ref_motifs, log_file, email, random_number)
    effective_command = 'echo %s > %s' %(command, log_file)
    result =  subprocess.Popen(effective_command, shell=True)
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
    email = request.form.get('email', '')
    email = email.replace(' ', '').rstrip()
    emailResponse = is_valid_email(email)
    textarea_input = request.form.get('SNPlist', '')
    uploaded_file = request.files.get('fasta_file')
    sequence_type = request.form.get('sequence_type', 'reads')  # Default value: reads
    min_k = request.form.get('min_k', '2')
    max_k = request.form.get('max_k', '10')
    figure = request.form.get('figure', 'True')
    msa = request.form.get('msa', 'Levenshtein')
    reverse = request.form.get('reverse', 'False')
    motif_guided = request.form.get('motif_guided', 'False')
    if sequence_type == "assembly":
        population_file = request.files.get('tsv_file')
    else: 
        population_file = None

    if motif_guided == "True":
        motif_input_file = request.files.get('motif_input')
    else: 
        motif_input_file = None

    if figure == "True":
        figure_format = request.form.get('format', 'pdf')
    else: 
        figure_format = 'pdf'

    # parse other inputs here
    if (textarea_input != '') or (uploaded_file and uploaded_file.filename != ''):
        if emailResponse == True:
            # if there was an input of some sort, create random number and output folder
            # generate random number
            random_number = random.randint(0, 1000000)
            # create output directory
            os.system('mkdir runs/run_%s' %(random_number))
            # message to the user with the run id
            #messageSubmission = 'Your job has been submitted with ID: %s. Copy your ID, you will need it to access your results.' %(random_number)
            messageSubmission = 'Your job has been submitted. We will send an email when the results are ready.'
            # then check what input that was
            if textarea_input != '':
                # write this file as it is the input for motifscope
                fout = open('runs/run_%s/run_%s_input.fa' %(random_number, random_number), 'w')
                fout.write(textarea_input)
                fout.close()
            elif uploaded_file and uploaded_file.filename != '':
                input_fasta = uploaded_file.read().decode('utf-8')
                fout = open('runs/run_%s/run_%s_input.fa' %(random_number, random_number), 'w')
                fout.write(input_fasta)
                fout.close()
            if population_file != None:
                population = population_file.read().decode('utf-8')
                fout = open('runs/run_%s/run_%s_population.txt' %(random_number, random_number), 'w')
                fout.write(population)
                fout.close()
            else:
                population = None
            if motif_input_file != None:
                ref_motifs = motif_input_file.read().decode('utf-8')
                fout = open('runs/run_%s/run_%s_motifs.txt' %(random_number, random_number), 'w')
                fout.write(ref_motifs)
                fout.close()
            else:
                ref_motifs = None
            # run the script here
            command = createMotifscopeCommand(random_number, sequence_type, population, min_k, max_k, figure, figure_format, msa, reverse, motif_guided, email)
            #command_run = subprocess.Popen(command, shell=True)
        else:
            messageSubmission = 'Email is not correct. Please check!'
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