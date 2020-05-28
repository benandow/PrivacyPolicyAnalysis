# PoliCheck


This repository hosts the source code for the PoliCheck tool. PoliCheck analyzes data flow to privacy policy consistency. Full details on the design of PoliCheck can be found in publication listed below.

# Instructions

* Place the plaintext privacy policies in /ext/plaintext\_policies

* Insert data flows in /ext/data/flows.csv. Example file included from data used in paper.

* Build the docker image: $ ./build.sh

* Run the docker image: $ ./run.sh

* See output CSV files in /ext/output directory

# Publication

Full details on PoliCheck can be found in the following publications:

Benjamin Andow, Samin Yaseer Mahmud, Justin Whitaker, William Enck, Bradley Reaves, Kapil Singh, and Serge Egelman. Actions Speak Louder than Words: Entity-Sensitive Privacy Policy and Data Flow Analysis with PoliCheck, Proceedings of the USENIX Security Symposium (SECURITY), August 2020, Boston, MA, USA.

Benjamin Andow, Samin Yaseer Mahmud, Wenyu Wang, Justin Whitaker, William Enck, Bradley Reaves, Kapil Singh, and Tao Xie. PolicyLint: Investigating Internal Privacy Policy Contradictions on Google Play, Proceedings of the USENIX Security Symposium (SECURITY), August 2019. Santa Clara, CA, USA.


# License

PoliCheck is licensed under the BSD-3-Clause License (See LICENSE.txt).
