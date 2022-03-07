# Privacy Policy Analysis (PolicyLint + PoliCheck)


This repository hosts the source code for both the PolicyLint and PoliCheck tool. PolicyLint identifies internal contradictions within privacy policies and PoliCheck analyzes data flow to privacy policy consistency. Full details on the design of PolicyLint and PoliCheck can be found in publications listed below.

# Instructions

* Place the plaintext privacy policies in ./ext/plaintext\_policies. Note that if you need to process HTML privacy policies, I recommend running a preprocessing step before to convert the policies to plaintext (e.g., https://github.com/benandow/HtmlToPlaintext).

* Insert a CSV representing the data flows into /ext/data/flows.csv. An example file is included from the data used within paper (./ext/data/flows.csv).

* Download the pretrained NLP model from https://drive.google.com/file/d/1yMB3TJt8oZX3-GHm9oB_eKU7oeJXfLbA/view?usp=sharing and place it in ./ext/NlpFinalModel

* Modify ./ext/run\_config to either specify "policylint" or "policheck" to set which ontologies the tool will leverage.

* Build the docker image: $ ./build.sh

* Run the docker image: $ ./run.sh

* See output CSV files in /ext/output directory

# Publication

Full details on PolicyLint and PoliCheck can be found in the following publications:

Benjamin Andow, Samin Yaseer Mahmud, Justin Whitaker, William Enck, Bradley Reaves, Kapil Singh, and Serge Egelman. Actions Speak Louder than Words: Entity-Sensitive Privacy Policy and Data Flow Analysis with PoliCheck, Proceedings of the USENIX Security Symposium (SECURITY), August 2020, Boston, MA, USA.

Benjamin Andow, Samin Yaseer Mahmud, Wenyu Wang, Justin Whitaker, William Enck, Bradley Reaves, Kapil Singh, and Tao Xie. PolicyLint: Investigating Internal Privacy Policy Contradictions on Google Play, Proceedings of the USENIX Security Symposium (SECURITY), August 2019. Santa Clara, CA, USA.


# License

PolicyLint/PoliCheck is licensed under the BSD-3-Clause License (See LICENSE.txt).
