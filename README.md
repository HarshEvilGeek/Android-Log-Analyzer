Android-Log-Analyzer
====================

A simple python script to analyze Android logs

Setup:

After you download the py script, modify the key_words to correspond to your app

app_marker_name = "all or part of your app name - com.example"
key_word_agent = "whatever identifies your agent logs"
key_word_device = "whatever identifies device info in your logs (if any)"

How to Use:

After you have modified the python script, pass the file/directory/zipfile you wish to analyze as the argument

python androidloganalyzer.py "your file" > output.txt

(you must have python installed) Please feel free to email me (akhilcherian@gmail.com) with any questions or suggestions

Currently requires Python 3.3+ , will modify to fix this
