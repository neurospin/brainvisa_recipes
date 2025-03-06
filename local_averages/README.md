To perform a local averages on the masked sulcal skeleton
---------------------------

For instance, to compute the average of the sulcal shape given a phenotype with `Average <https://github.com/neurospin-projects/2024_adufournet_sulcus_genetics/blob/ad279118/notebooks/MOStest/Interpretation/Moving_average.py>`_, you need the BrainVISA environment.
In this example, we work with the number of allele C as the phenotype.
The region is the anterior cingulate cortex (CINGULATE.).
The hemisphere is the left (L).
The subjects ID are in the IID column (IID).
The phenotype is in the column projection.
The 200-subjects averages will be plot on 2 columns, 1 row.

.. code-block:: shell

   bv bash
   cd notebooks
   python3 MOStest/Interpretation/Moving_average.py -p path_to_regression_on_rs4842267_C.csv \
                                                    -r CINGULATE. \
                                                    -i L \
                                                    -s IID \
                                                    -e projection \
                                                    -n 2 \
                                                    -l 1 \
                                                    -t 200 
