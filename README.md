1. Executing the python script 'extract_emails_from_papers.py' will ask the user to enter the name of the scientific publication (example : 'Visualizing and understanding neural models in NLP') he or she wants to extract email addresses from. 
2. The user Microsoft Academic Graph to find links to the PDF, so the user will need an Microsoft Azure account and keys for accessing the Microsoft Academic Graph API.
3. The user will need to replace 'xxxx' for the key 'Ocp-Apim-Subscription-Key' in the 'headers' dictionary in the function get_emails to be able to run the script and perform the end goal of extracting emails from publications.
4. The way the functionality works is as follows :
* the name of the publication input by the user is used to search for the publication's metadata in Microsoft Academic Graph.
* The link for the pdf is searched for among the metadata
* The pdf is downloaded from the extracted link and the contents are converted to text
* The text is broken into tokens and these tokens are examined using regular expressions to identify and return the email addresses.
  
