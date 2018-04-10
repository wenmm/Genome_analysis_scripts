#! python3
# gff3_to_fasta.py
# A not-as-simple-as-wanted python program which reads a genome fasta file and corresponding gff3 file
# in a format output by PASA and retrieves the main and/or alternative isoform transcripts from each locus

import os, argparse, re
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.Alphabet import generic_dna

# Define functions for later use
def reverse_comp(seq):
        reversedSeq = seq[::-1].lower()
        # Decode characters
        reversedSeq = reversedSeq.replace('a', 'T')
        reversedSeq = reversedSeq.replace('t', 'A')
        reversedSeq = reversedSeq.replace('c', 'G')
        reversedSeq = reversedSeq.replace('g', 'C')
        return reversedSeq

def group_process(currGroup):
        full_mrnaGroup = []             # This will hold processed mRNA positions
        mrnaGroup = []                  # This will be a temporary storage for mRNA lines
        for entry in currGroup:
                # Handle the first line in the group: we just want the gene ID
                if entry[2] == 'gene':
                        geneID = idRegex.search(entry[8]).group(1)
                # Handle mRNA lines: this will start a subgroup corresponding to the mRNA
                elif entry[2] == 'mRNA':
                        if mrnaGroup == []:             # i.e., if this is the first mRNA line in this gene group, we just need to start building it
                                mrnaGroup.append(entry)
                        else:                           # i.e., there is more than one mRNA in this gene group, so we need to process the group we've built then initiate a new one
                                # Process current mrnaGroup
                                for subentry in mrnaGroup:
                                        if seqType != 'cds':
                                                if subentry[2] == 'mRNA':
                                                        full_mrnaGroup.append([idRegex.search(subentry[8]).group(1), []])
                                                elif subentry[2] != 'CDS':              # CDS lines are the only one we don't care about - we just grab the exon since its identical / more relevant
                                                        coords = subentry[3] + '-' + subentry[4]        # +1 here to make Python act 1-based like gff3 format
                                                        full_mrnaGroup[-1][-1].append(coords)
                                        else:
                                                if subentry[2] == 'mRNA':
                                                        full_mrnaGroup.append([idRegex.search(subentry[8]).group(1), []])
                                                elif subentry[2] == 'CDS':
                                                        coords = subentry[3] + '-' + subentry[4]        # +1 here to make Python act 1-based like gff3 format
                                                        full_mrnaGroup[-1][-1].append(coords)
                                # Initiate new mrnaGroup
                                full_mrnaGroup[-1] += [subentry[0],subentry[6]]          # Append contig ID and orientation
                                mrnaGroup = [entry]
                else:
                        mrnaGroup.append(entry)
        # Process the mrnaGroup that's currently sitting in the pipe (so to speak)
        for subentry in mrnaGroup:
                if seqType != 'cds':
                        if subentry[2] == 'mRNA':
                                full_mrnaGroup.append([idRegex.search(subentry[8]).group(1), []])
                        elif subentry[2] != 'CDS':              # CDS lines are the only one we don't care about - we just grab the exon since its identical / more relevant
                                coords = subentry[3] + '-' + subentry[4]        # +1 here to make Python act 1-based like gff3 format
                                full_mrnaGroup[-1][-1].append(coords)
                else:
                        if subentry[2] == 'mRNA':
                                full_mrnaGroup.append([idRegex.search(subentry[8]).group(1), []])
                        elif subentry[2] == 'CDS':
                                coords = subentry[3] + '-' + subentry[4]        # +1 here to make Python act 1-based like gff3 format
                                full_mrnaGroup[-1][-1].append(coords)
        full_mrnaGroup[-1] += [subentry[0],subentry[6]]          # Append contig ID and orientation
        # Put info into the coordDict and move on
        gffCoordDict[geneID] = full_mrnaGroup

##### USER INPUT SECTION

usage = """%(prog)s reads in genome fasta file and corresponding gff3 file in a format output by PASA and retrieves the main
and/or alternative isoform transcripts or CDS' for each locus. Alternatively, you can grab the CDS regions which will produce nucleotide
and AA files (name format == OUTPUT.nucl / OUTPUT.aa)
"""
p = argparse.ArgumentParser(description=usage)
p.add_argument("-i", "-input", dest="fasta",
                  help="genome fasta file")
p.add_argument("-g", "-gff", dest="gff3",
                  help="gff3 file")
p.add_argument("-l", "-locusSeqs", dest="locusSeqs", choices = ['main', 'isoforms'],
                  help="type of transcripts to extract from each locus (main == just the ")
p.add_argument("-s", "-seqType", dest="seqType", choices = ['transcripts', 'cds'],
                  help="type of sequence to output (transcripts == full gene model including UTRs if annotated, cds == coding regions)")
p.add_argument("-o", "-output", dest="output",
             help="output fasta file name containing transcript sequences")
p.add_argument("-f", "-force", dest="force", choices = ['y', 'n', 'Y', 'N'],
               help="default == 'n', which means the program will not overwrite existing files. Specify 'y' to allow this behaviour at your own risk.", default='n')

args = p.parse_args()

# Obtain data from arguments
fastaFile = args.fasta
gffFile = args.gff3
locusSeqs = args.locusSeqs
seqType = args.seqType
outputFileName = args.output
force = args.force

# Format cds output names if relevant
if seqType == 'cds':
        nuclOutputFileName = outputFileName + '.nucl'
        protOutputFileName = outputFileName + '.aa'

# Check that output won't overwrite another file
if seqType != 'cds':
        if os.path.isfile(outputFileName) and force.lower() != 'y':
                print('There is already a file named ' + outputFileName + '. Either specify a new file name, delete these older file(s), or provide the -force argument either "Y" or "y"')
                quit()
        elif os.path.isfile(outputFileName) and force.lower() == 'y':
                os.remove(outputFileName)
else:
        # Nucl
        if os.path.isfile(nuclOutputFileName) and force.lower() != 'y':
                print('There is already a file named ' + nuclOutputFileName + '. Either specify a new file name, delete these older file(s), or provide the -force argument either "Y" or "y"')
                quit()
        elif os.path.isfile(nuclOutputFileName) and force.lower() == 'y':
                os.remove(nuclOutputFileName)
        # Prot
        if os.path.isfile(protOutputFileName) and force.lower() != 'y':
                print('There is already a file named ' + protOutputFileName + '. Either specify a new file name, delete these older file(s), or provide the -force argument either "Y" or "y"')
                quit()
        elif os.path.isfile(protOutputFileName) and force.lower() == 'y':
                os.remove(protOutputFileName)

# Load the fasta file and parse its contents
seqFile = open(fastaFile, 'rU')
records = SeqIO.to_dict(SeqIO.parse(seqFile, 'fasta'))

# Parse the gff3 file
idRegex = re.compile(r'ID=(.+?);')
currGroup = []
gffCoordDict = {}
pasaProts = {}                  # We use this to get amino acid translations since 5' fragmented CDS regions will be incorrectly translated if we derive it from the sequence itself
with open(gffFile, 'r') as fileIn:
        for line in fileIn:
                # Skip filler lines
                if line == '\n':
                        continue
                # Grab the PASA predicted ORF sequences
                if line.startswith('#PROT'):
                        sl = line.rstrip('\n').split('\t')
                        geneID = sl[0].split()[1]
                        pasaProt = sl[1]
                        pasaProts[geneID] = pasaProt
                        continue
                elif line.startswith('#'):
                        continue
                # Get details
                sl = line.rstrip('\n').split('\t')
                lineType = sl[2]
                idCell = sl[8]
                # Building gene group/process it
                if lineType == 'gene':
                        if currGroup == []:
                                # First iteration: just play it cool, add the sl to the group
                                currGroup.append(sl)
                                continue
                        else:
                                # Process group if we're encountering a new group
                                group_process(currGroup)
                                currGroup = [sl]
                elif lineType == 'rRNA' or lineType == 'tRNA':          # Skip lines that aren't coding
                        continue
                else:
                        # Keep building group until we encounter another 'gene' lineType
                        currGroup.append(sl)
        # Process the last mrnaGroup
        group_process(currGroup)

# Prepare results
if seqType != 'cds':
        outList = []
else:
        nuclOutList = []
        protOutList = []

for key, value in gffCoordDict.items():
        skipped = 'y'
        # Handle picking out the main/representative gene based on length
        if locusSeqs == 'main':
                longestMrna = ['', 0]           # We pick out the representative gene based on length. If length is identical, we'll end up picking the entry listed first in the gff3 file since our > condition won't be met. I doubt this will happen much or at all though.
                for mrna in value:
                        mrnaLen = 0
                        for pair in mrna[1]:
                                coords = pair.split('-')
                                mrnaLen += (int(coords[1]) - int(coords[0]) + 1)
                        if mrnaLen > longestMrna[1]:
                                longestMrna = [mrna, mrnaLen]
                value = [longestMrna[0]]          # This will mean we only have one entry in value for when we iterate through this below, ensuring we get just the representative gene
        for mrna in value:
                skipped = 'n'
                try:
                        genomeSeq = str(records[mrna[2]].seq)
                except:
                        print(value)
                        quit()
                # Join sequence segments
                if mrna[3] == '-':
                        mrna[1].reverse()
                transcript = ''
                for pair in mrna[1]:
                        coords = pair.split('-')
                        segment = genomeSeq[int(coords[0])-1:int(coords[1])]            # Make it 1-based by -1 to the first coordinate
                        transcript += segment
                # Reverse comp if necessary
                if mrna[3] == '-':
                        transcript = reverse_comp(transcript)
                # Get protein translation if necessary
                if seqType == 'cds':
                        #aatranscript = str(Seq(transcript, generic_dna).translate(table=1))
                        aatranscript = pasaProts[mrna[0]]                               # As mentioned before, directly translating the ORF may cause nonsense if a fragmentary CDS isn't in frame 1
                # Output to file
                if seqType != 'cds':
                        outList.append('>' + mrna[0] + '\n' + transcript)
                else:
                        nuclOutList.append('>' + mrna[0] + '\n' + transcript)
                        protOutList.append('>' + mrna[0] + '\n' + aatranscript)
        # Debug: check if we skipped a mRNA
        if skipped == 'y':
                print('Dun goofed!')
                print(key)
                print(value)
                quit()

# Dump to file
if seqType != 'cds':
        with open(outputFileName, 'w') as fileOut:
                fileOut.write('\n'.join(outList))
else:
        with open(nuclOutputFileName, 'w') as nuclOut, open(protOutputFileName, 'w') as protOut:
                nuclOut.write('\n'.join(nuclOutList))
                protOut.write('\n'.join(protOutList))

#### SCRIPT ALL DONE, GO HOME
