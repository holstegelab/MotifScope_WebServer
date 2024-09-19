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
def createMotifscopeCommand(random_number, cluster, class_tsv, min_k, max_k, figure, figure_format, msa, reverse, ref_motifs, email):
    # define input reads
    output_folder = f'runs/run_{random_number}'
    output_prefix = f"{output_folder}/run_{random_number}_output"
    output_figure = f'{output_folder}/run_{random_number}_output.{figure_format}'
    keep_figure = f'runs/run_{random_number}_output.{figure_format}'



    log_file = f'{output_folder}/run_{random_number}_output.log'
    input_reads = f'{output_folder}/run_{random_number}_input.fa'
    output_compressed = f'runs/run_{random_number}.zip'

    options = []
    if class_tsv:
        cls_file = f'{output_folder}/run_{random_number}_class.txt'    
        options.append(f'-p {cls_file}')

    if ref_motifs:
        motiffile = f'{output_folder}/run_{random_number}_motifs.txt'
        options.append(f'-motif {motiffile}')

    
    command = f"""motifscope -c {cluster} -i {input_reads} -mink {min_k} -maxk {max_k} -o {output_prefix} -figure {figure} -format {figure_format} -r 1 -msa {msa} -reverse {reverse} {' '.join(options)} >> {log_file} 2>&1; 
                  echo 'process is done'; 
                  zip -r {output_compressed} {output_folder}; 
                  if [ -f {output_figure} ]; then mv {output_figure} {keep_figure}; fi;
                  rm -rf {output_folder}; 
                  python3 send_email.py {email} {random_number}"""

    effective_command = 'echo "%s" > %s' %(command, log_file)
    effective_command_log = subprocess.Popen(effective_command, shell=True)
    return command

# function to check whether the run_id is correct
def check_runID(run_id):
    run_id = run_id.replace(' ', '')
    if run_id == '':
        messageError = True
        messageToUser = 'Please insert a valid Run ID'
    else:
        try: #validate that run id is an integer
            run_id = int(run_id)
            run_id = str(run_id)
        except:
            messageError = True
            messageToUser = 'Not valid Run ID. Try again.'
            return messageError, messageToUser

        # check whether the file exists
        if os.path.exists('runs/run_%s.zip' %(run_id)):
            messageError = False
            messageToUser = 'Valid Run ID. Download will start soon'
            # compress folder and remove original folder
        else:
            messageError = True
            messageToUser = 'The results are not ready yet, or this is not a valid run ID. Try again later.'

    # get run zip files from runs folder, and remove those that are older than 1 month
    os.system('find runs/ -name "*.zip" -mtime +31 -delete')
    os.system('find runs/ -name "*.pdf" -mtime +31 -delete')
    return messageError, messageToUser

# Create a Flask app instance
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024 #max 4 mb

# Annotation section
@app.route('/', methods=["GET", "POST"])
@app.route('/index/', methods=["GET", "POST"])
def index():
    # read inputs
    email = request.form.get('email', '')
    email = email.replace(' ', '').rstrip()
    emailResponse = is_valid_email(email)

    textarea_input = request.form.get('fasta_text', '')
    uploaded_file = request.files.get('fasta_file')
    
    cluster = request.form.get('cluster', 'True')

    min_k = request.form.get('min_k', '2')
    max_k = request.form.get('max_k', '10')

    figure = request.form.get('figure', 'True')
    msa = request.form.get('msa', 'Levenshtein')

    reverse = request.form.get('reverse', 'False')

    class_file = request.files.get('class_file')
    motif_input_file = request.files.get('motif_input')

    if figure == "True":
        figure_format = request.form.get('format', 'pdf')
    else: 
        figure_format = 'pdf'

    # parse other inputs here
    if (textarea_input != '') or (uploaded_file and uploaded_file.filename != ''):
        if emailResponse == True:
            # if there was an input of some sort, create random number and output folder
            # generate random number
            random_number = random.randint(0, 1000000000)
            # create output directory
            os.system('mkdir runs/run_%s' %(random_number))
            # message to the user with the run id
            #messageSubmission = 'Your job has been submitted with ID: %s. Copy your ID, you will need it to access your results.' %(random_number)
            messageSubmission = f'Your job has been submitted with ID {random_number}. Check the Download page shortly to get your results.\n We will also send an email to notify you when the results are ready.'
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
            if class_file != None:
                class_tsv = class_file.read().decode('utf-8').strip()
                fout = open('runs/run_%s/run_%s_class.txt' %(random_number, random_number), 'w')
                fout.write(class_tsv)
                fout.close()
            else:
                class_tsv = None

            if motif_input_file != None:
                ref_motifs = motif_input_file.read().decode('utf-8').strip()
                fout = open('runs/run_%s/run_%s_motifs.txt' %(random_number, random_number), 'w')
                fout.write(ref_motifs)
                fout.close()
            else:
                ref_motifs = None
            # run the script here
            command = createMotifscopeCommand(random_number, cluster, class_tsv, min_k, max_k, figure, figure_format, msa, reverse, ref_motifs, email)
            command_run = subprocess.Popen(command, shell=True)
        else:
            messageSubmission = 'Email is not correct. Please check!'
    else:
        messageSubmission = ''
    return render_template('index.html', messageSubmission=messageSubmission) 

def figure_exist(run_id):
    filename = f"run_{run_id}_output.pdf"
    filepath = os.path.join("runs", filename)
    if not os.path.exists(filepath):
        filename = f"run_{run_id}_output.png"
        filepath = os.path.join("runs", filename)
    return os.path.exists(filepath)


# Download tab
@app.route('/download/', methods=["GET", "POST"])
def download():
    run_id = None
    messageError = None
    messageToUser = None
    fig_exists = False
    if request.method == 'POST':
        run_id = request.form["run_id"]
        messageError, messageToUser = check_runID(run_id)
        fig_exists = figure_exist(run_id)
    return render_template('download.html', run_id=run_id, figure_exists=fig_exists, messageError=messageError, messageToUser=messageToUser)

# Actual download button for the annotation results
@app.route('/downloadResults/<run_id>', methods=["GET"])
def download_results(run_id):
    # check here the run ID
    try:
        run_id = int(run_id)
    except:
        return render_template('download.html', run_id=run_id, messageError=True, messageToUser='Not a valid Run ID. Try again.')

    filename = f"run_{run_id}.zip"
    filepath = os.path.join("runs", filename)
    return send_file(filepath, as_attachment=True, download_name=filename)

# Actual download button for the annotation results
@app.route('/downloadFigure/<run_id>', methods=["GET"])
def download_figure(run_id):
    # check here the run ID
    try:
        run_id = int(run_id)
    except:
        return render_template('download.html', run_id=run_id, messageError=True, messageToUser='Not a valid Run ID. Try again.')

    filename = f"run_{run_id}_output.pdf"
    filepath = os.path.join("runs", filename)
    if not os.path.exists(filepath):
        filename = f"run_{run_id}_output.png"
        filepath = os.path.join("runs", filename)
    if not os.path.exists(filepath):
        return render_template('download.html', run_id=run_id, messageError=True, messageToUser='No figure was generated. If this is unexpected, check the log file in the annotation download.')
    return send_file(filepath, as_attachment=False, download_name=filename)

@app.route('/about/', methods=["GET"])
def about():
    return render_template("about.html")

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
