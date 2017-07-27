#!/usr/bin/env python3


import gzip
import io
import pickle
import os
from argparse import ArgumentParser


def reverse_complement(sequence):
    complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A', 'N': 'N', 'M': 'K', 'R': 'Y', 'W': 'W',
                            'S': 'S', 'Y': 'R', 'K': 'M', 'V': 'B', 'H': 'D', 'D': 'H', 'B': 'V'}
    return "".join(complement[base] for base in reversed(sequence))


def parse_args():
    "Parse the input arguments, use '-h' for help."
    parser = ArgumentParser(description='SalmID - rapid Kmer based Salmonella identifier from raw data')
    # inputs
    parser.add_argument(
        '-i','--input', nargs='+', type=str, required=False, default= 'None',
        help='Single fastq.gz file input, include path to file if file is not in same directory ')
    parser.add_argument(
        '-e', '--extension', nargs='+', type=str, required=False, default=['.fastq.gz'],
        help='File extension, if specified without "--input_dir", SalmID will attempt to ID all files\n' +
             ' with this extension in current directory, otherwise files in input directory')

    parser.add_argument(
        '-d','--input_dir', nargs='+', type=str, required=False, default='.',
        help='Directory which contains data for identification, when not specified files in current directory will be analyzed.')
    return parser.parse_args()


def createKmerDict_reads(list_of_strings, kmer):
    kmer_table = {}
    for string in list_of_strings:
        sequence = string.strip('\n')
        for i in range(len(sequence)-kmer+1):
            new_mer =sequence[i:i+kmer]
            new_mer_rc = reverse_complement(new_mer)
            if new_mer in kmer_table:
                kmer_table[new_mer.upper()] += 1
            else:
                kmer_table[new_mer.upper()] = 1
            if new_mer_rc in kmer_table:
                kmer_table[new_mer_rc.upper()] += 1
            else:
                kmer_table[new_mer_rc.upper()] = 1
    return kmer_table


def target_read_kmerizer_multi(file, k, kmerDict_1, kmerDict_2):
    mean_1 = None
    mean_2 = None
    i = 1
    n_reads_1 = 0
    n_reads_2 = 0
    total_coverage_1 = 0
    total_coverage_2 = 0
    reads_1 = []
    reads_2 = []
    for line in io.BufferedReader(gzip.open(file)):
        start = int((len(line) - k) // 2)
        if i % 4 == 2:
            s1 = line[start:k + start].decode()
            if s1 in kmerDict_1:
                n_reads_1 += 1
                total_coverage_1 += len(line)
                reads_1.append(line.decode())
            if s1 in kmerDict_2:
                n_reads_2 += 1
                total_coverage_2 += len(line)
                reads_2.append(line.decode())
        i += 1
        if total_coverage_2 >= 20000:
            break

    if len(reads_1) == 0:
        kmer_Dict1 = {}
    else:
        kmer_Dict1 = createKmerDict_reads(reads_1, k)
        mers_1 = set([key for key in kmer_Dict1])
        mean_1 = sum([kmer_Dict1[key] for key in kmer_Dict1])/len(mers_1)
    if len(reads_2) == 0:
        kmer_Dict2 = {}
    else:
        kmer_Dict2 = createKmerDict_reads(reads_2, k)
        mers_2 = set([key for key in kmer_Dict2])
        mean_2 = sum([kmer_Dict2[key] for key in kmer_Dict2])/len(mers_2)
    return kmer_Dict1, kmer_Dict2, mean_1, mean_2

def mean_cov_selected_kmers(iterable, kmer_dict, clade_specific_kmers):
    '''
    Given an iterable (list, set, dictrionary) returns mean coverage for the kmers in iterable
    :param iterable: set, list or dictionary containing kmers
    :param kmer_dict: dictionary with kmers as keys, kmer-frequency as value
    :param  clade_specific_kmers: list, dict or set of clade specific kmers
    :return: mean frequency as float
    '''
    if len(iterable) == 0:
        return 0
    return sum([kmer_dict[value] for value in iterable])/len(clade_specific_kmers)

def kmer_lists(query_fastq_gz, k,
               allmers,allmers_rpoB,
               uniqmers_bongori,
               uniqmers_I,
               uniqmers_IIa,
               uniqmers_IIb,
               uniqmers_IIIa,
               uniqmers_IIIb,
               uniqmers_IV,
               uniqmers_VI,
               uniqmers_VII,
               uniqmers_VIII,
               uniqmers_bongori_rpoB,
               uniqmers_S_enterica_rpoB,
               uniqmers_Escherichia_rpoB,
               uniqmers_Listeria_ss_rpoB,
               uniqmers_Lmono_rpoB):
    dict_invA, dict_rpoB, mean_invA, mean_rpoB = target_read_kmerizer_multi(query_fastq_gz, k, allmers,
                                                                            allmers_rpoB)
    target_mers_invA = set([key for key in dict_invA])
    target_mers_rpoB = set([key for key in dict_rpoB])
    # target_mers_rpoB = target_read_kmerizer(query_fastq_gz, 27, allmers_rpoB)
    if target_mers_invA == 0:
        print('No reads found matching invA, no Salmonella in sample?')
    else:
        p_bongori = (len(uniqmers_bongori & target_mers_invA) / len(uniqmers_bongori)) * 100
        p_I = (len(uniqmers_I & target_mers_invA) / len(uniqmers_I)) * 100
        p_IIa = (len(uniqmers_IIa & target_mers_invA) / len(uniqmers_IIa)) * 100
        p_IIb = (len(uniqmers_IIb & target_mers_invA) / len(uniqmers_IIb)) * 100
        p_IIIa = (len(uniqmers_IIIa & target_mers_invA) / len(uniqmers_IIIa)) * 100
        p_IIIb = (len(uniqmers_IIIb & target_mers_invA) / len(uniqmers_IIIb)) * 100
        p_VI = (len(uniqmers_VI & target_mers_invA) / len(uniqmers_VI)) * 100
        p_IV = (len(uniqmers_IV & target_mers_invA) / len(uniqmers_IV)) * 100
        p_VII = (len(uniqmers_VII & target_mers_invA) / len(uniqmers_VII)) * 100
        p_VIII = (len(uniqmers_VIII & target_mers_invA) / len(uniqmers_VIII)) * 100
        p_bongori_rpoB = (len(uniqmers_bongori_rpoB & target_mers_rpoB) / len(uniqmers_bongori_rpoB)) * 100
        p_Senterica = (len(uniqmers_S_enterica_rpoB & target_mers_rpoB) / len(uniqmers_S_enterica_rpoB)) * 100
        p_Escherichia = (len(uniqmers_Escherichia_rpoB & target_mers_rpoB) / len(uniqmers_Escherichia_rpoB)) * 100
        p_Listeria_ss = (len(uniqmers_Listeria_ss_rpoB & target_mers_rpoB) / len(uniqmers_Listeria_ss_rpoB)) * 100
        p_Lmono = (len(uniqmers_Lmono_rpoB & target_mers_rpoB) / len(uniqmers_Lmono_rpoB)) * 100
        bongori_invA_cov = mean_cov_selected_kmers(uniqmers_bongori & target_mers_invA, dict_invA, uniqmers_bongori)
        I_invA_cov = mean_cov_selected_kmers(uniqmers_I & target_mers_invA, dict_invA, uniqmers_I)
        IIa_invA_cov = mean_cov_selected_kmers(uniqmers_IIa & target_mers_invA, dict_invA, uniqmers_IIa)
        IIb_invA_cov = mean_cov_selected_kmers(uniqmers_IIb & target_mers_invA, dict_invA, uniqmers_IIb)
        IIIa_invA_cov = mean_cov_selected_kmers(uniqmers_IIIa & target_mers_invA, dict_invA, uniqmers_IIIa)
        IIIb_invA_cov = mean_cov_selected_kmers(uniqmers_IIIb & target_mers_invA, dict_invA, uniqmers_IIIb)
        IV_invA_cov = mean_cov_selected_kmers(uniqmers_IV & target_mers_invA, dict_invA, uniqmers_IV)
        VI_invA_cov = mean_cov_selected_kmers(uniqmers_VI & target_mers_invA, dict_invA, uniqmers_VI)
        VII_invA_cov = mean_cov_selected_kmers(uniqmers_VII & target_mers_invA, dict_invA, uniqmers_VII)
        VIII_invA_cov = mean_cov_selected_kmers(uniqmers_VIII & target_mers_invA, dict_invA, uniqmers_VIII)
        S_enterica_rpoB_cov = mean_cov_selected_kmers((uniqmers_S_enterica_rpoB & target_mers_rpoB), dict_rpoB,
                                                      uniqmers_S_enterica_rpoB)
        S_bongori_rpoB_cov = mean_cov_selected_kmers((uniqmers_bongori_rpoB & target_mers_rpoB), dict_rpoB,
                                                     uniqmers_bongori_rpoB)
        Escherichia_rpoB_cov = mean_cov_selected_kmers((uniqmers_Escherichia_rpoB & target_mers_rpoB), dict_rpoB,
                                                       uniqmers_Escherichia_rpoB)
        Listeria_ss_rpoB_cov = mean_cov_selected_kmers((uniqmers_Listeria_ss_rpoB & target_mers_rpoB), dict_rpoB,
                                                       uniqmers_Listeria_ss_rpoB)
        Lmono_rpoB_cov = mean_cov_selected_kmers((uniqmers_Lmono_rpoB & target_mers_rpoB), dict_rpoB,
                                                 uniqmers_Lmono_rpoB)
        coverages = [Listeria_ss_rpoB_cov, Lmono_rpoB_cov, S_bongori_rpoB_cov, S_enterica_rpoB_cov,
                     Escherichia_rpoB_cov, bongori_invA_cov, I_invA_cov,IIa_invA_cov, IIb_invA_cov,
                     IIIa_invA_cov, IIIb_invA_cov, IV_invA_cov, VI_invA_cov, VII_invA_cov,
                     VIII_invA_cov]
        locus_scores = [p_Listeria_ss, p_Lmono, p_Escherichia, p_bongori_rpoB, p_Senterica, p_bongori,
                        p_I, p_IIa,p_IIb, p_IIIb, p_IIIa, p_IV, p_VI, p_VII, p_VIII]
    return locus_scores, coverages


def main():
    #todo: introduce single and batch modes, batch mode with or without
    ex_dir = os.path.dirname(os.path.realpath(__file__))
    args = parse_args()
    input = args.input[0]
    if input != 'N':
        files = [input]
    else:
        extension = args.extension[0]
        inputdir = args.input_dir[0]
        files = [inputdir + '/'+ f for f in os.listdir(inputdir) if f.endswith(extension)]
    f_invA = open(ex_dir + "/invA_mers_dict", "rb")
    sets_dict_invA = pickle.load(f_invA)
    f_invA.close()
    allmers = sets_dict_invA['allmers']
    uniqmers_I = sets_dict_invA['uniqmers_I']
    uniqmers_IIa = sets_dict_invA['uniqmers_IIa']
    uniqmers_IIb = sets_dict_invA['uniqmers_IIb']
    uniqmers_IIIa = sets_dict_invA['uniqmers_IIIa']
    uniqmers_IIIb = sets_dict_invA['uniqmers_IIIb']
    uniqmers_IV = sets_dict_invA['uniqmers_IV']
    uniqmers_VI = sets_dict_invA['uniqmers_VI']
    uniqmers_VII = sets_dict_invA['uniqmers_VII']
    uniqmers_VIII = sets_dict_invA['uniqmers_VIII']
    uniqmers_bongori = sets_dict_invA['uniqmers_bongori']

    f = open(ex_dir + "/rpoB_mers_dict", "rb")
    sets_dict = pickle.load(f)
    f.close()

    allmers_rpoB = sets_dict['allmers']
    uniqmers_bongori_rpoB = sets_dict['uniqmers_bongori']
    uniqmers_S_enterica_rpoB = sets_dict['uniqmers_S_enterica']
    uniqmers_Escherichia_rpoB = sets_dict['uniqmers_Escherichia']
    uniqmers_Listeria_ss_rpoB = sets_dict['uniqmers_Listeria_ss']
    uniqmers_Lmono_rpoB = sets_dict['uniqmers_L_mono']
    print(
        'file\tListeria sensu stricto (rpoB)\tL. monocytogenes (rpoB)\tEscherichia spp. (rpoB)\tS. bongori (rpoB)\tS. enterica' +
        '(rpoB)\tS. bongori (invA)\tsubsp. I (invA)\tsubsp. IIa (invA)\tsubsp. IIb' +
        ' (invA)\tsubsp. IIIa (invA)\tsubsp. IIIb (invA)\tsubsp.IV (invA)\tsubsp. VI (invA)\tsubsp. VII (invA)' +
        '\tsubsp. VIII (prov.) (invA)')
    for f in files:
        locus_scores, coverages = kmer_lists( f, 27,
                   allmers,allmers_rpoB,
                   uniqmers_bongori,
                   uniqmers_I,
                   uniqmers_IIa,
                   uniqmers_IIb,
                   uniqmers_IIIa,
                   uniqmers_IIIb,
                   uniqmers_IV,
                   uniqmers_VI,
                   uniqmers_VII,
                   uniqmers_VIII,
                   uniqmers_bongori_rpoB,
                   uniqmers_S_enterica_rpoB,
                   uniqmers_Escherichia_rpoB,
                   uniqmers_Listeria_ss_rpoB,
                   uniqmers_Lmono_rpoB)
        if sum(locus_scores) == 0:
            print(f.split('/')[-1] + ' does not contain Salmonella, Escherichia or Listeria sensu stricto')
        else:
            pretty_scores = [str(round(score)) for score in locus_scores]
            print(f.split('/')[-1] +'\t' + '\t'.join(pretty_scores))

if __name__ == '__main__':
    main()

