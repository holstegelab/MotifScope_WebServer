# Set up variables
INPUT_FA=$1
OUTPUT_DIR=$2

# TREAT case-control analysis command
docker run -it --rm \
        -v ${INPUT_FA}:/run_input.fa \
        -v ${OUTPUT_DIR}:/output_dir \
        motifscope \
        --sequence-type reads \
        -i /run_input.fa \
        -mink 2 \
        -maxk 10 \
        -o /output_dir/example \
        -msa POAMotif