# SeqMatrix

This PyQt5 GUI is to facilitize the sort of multigenes dataset.

![image](https://github.com/user-attachments/assets/242cf17f-19bf-4575-bbb9-ef874fe567f1)

In multigene phylogeny (especially a small-scale dataset), it usually takes a lot of time to rename sequences belonging to a same isolation or voucher. The author himself was once very annoyed about it, so free-concatenator is given birth.

In this PyQt5 GUI, you can load lots of FASTA sequences from multiple files and create a specific-scale dataset (each column refers to a partition, while each row refers to a single isolate or voucher). Then you may drag each FASTA sequence from the left column to a specific grid of the dataset table to sort sequences fast. What's more, directly fill in a grid with NCBI Accession (Genebank or Refseq or etc) is okay. Then press the 'Download from NCBI' button and the program may try to download all accession's fasta sequences and automatically replace the original grids with the sequences.

If you have a ready-made accession table, you can paste a column directly to the first grid of each column and press 'Format Cells', which splits the pasted text by line breaks and distribute each children to a grid in order. Then you may press 'Download from NCBI' to form your dataset directly.

Once your dataset is ready, press 'Export Files' to get fasta files of each partition, which can be aligned and concatenated directly.

# Dependance

```plain
pip install PyQt5, Bio
```

# Acknowledgements

I thank Cursor Team for providing a wonderful AI-assisted IDE, where I quickly formed the initial version of this script in about 15 mins with the help of Claude 3.5 sonnet, in my busy time.
