import http.client, urllib.request, urllib.parse, urllib.error, base64
import json
import os
import re
import sys
import ast


def get_pdf_contents(download_url):
    global processing_errors

    try:
        response = urllib.request.urlopen(download_url)
    except:  # deals with downloading errors
        e = sys.exc_info()
        print("-------PDF FILE CANNOT BE DOWNLOADED--------and the link is", download_url, "error is %e", e)
        return ([],
                0)  # alerts the calling function that the link that was passed to it for processing couldn't be handled correctly
    file = open("doc_final.pdf",
                'wb')  # write the pdf that was downloaded into a file for conversion into .txt format for extarcting emails
    file_contents = response.read()
    file.write(file_contents)
    file.close()
    os.system('pdftotext doc_final.pdf')
    # deals with errors relating to converting the pdf to .txt format
    try:
        file = open("doc_final.txt", "r")
    except:
        print("The downloaded url was not processed")
        return ([],
                0)  # alerts the calling function that the link that was passed to it for processing couldn't be handled correctly
    text = file.read()
    return text


def get_emails_from_text(text):
    fptr = open('url_extensions.txt', "r")
    list_of_urls = ast.literal_eval(fptr.read())
    list_of_urls.remove('cs')
    tokens = text.split()
    new_tokens = []
    # split the whole .txt converted pdf into tokens for facilitating extraction of emails
    for item in tokens:
        for token in item.split(","):
            if (len(token) > 0):
                new_tokens.append(token)
    emaillist = []

    # the following code conatins regular expressions for identifying and extracting emails in different formats
    pattern = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"  # regular expression for extraction of emails in trivial format i.e.each email is present as a single independent token of the form  a@b.c
    for i in range(len(new_tokens)):
        inst = re.findall(pattern, new_tokens[i])  # for when the email address is trivially present as a single token and a simple regular expression can enable extraction of emails
        if (inst):
            emaillist.append(inst[0])
        emaillist2 = []
        if (re.findall(r"[a-zA-Z0-9]}@", new_tokens[
            i])):  # (1)for when multiple email addresses are present non trivially in the form {a,b,c}@d.e
            address_extension = new_tokens[i].split("}")[1]
            name = new_tokens[i].split("}")[0]
            if (re.findall(r"{", name)):
                name = name.split("{")[1]
                look = 0
            else:
                look = 1
            emaillist2.append(name + address_extension)
            j = i - 1
            while ((len(re.findall(r"{", new_tokens[j])) == 0) & (look == 1) & (j >= 1)):
                emaillist2.append(new_tokens[j] + address_extension)
                j = j - 1
            if ((look == 1) & (j == 0)):
                emaillist2 = []
            emaillist2.reverse()
            emaillist.extend(emaillist2)
        at = re.findall(r"^@$|^AT$", new_tokens[i])
        if (
                at):  # (2)for when multiple email addresses are present non trivially in the form a AT b DOT c or a @ b . c (space separated)
            if (new_tokens[i - 2] == "." or new_tokens[i - 2] == "DOT"):
                email_string = new_tokens[i - 3] + "." + new_tokens[i - 1] + '@'
            else:
                email_string = new_tokens[i - 1] + '@'
            for j in range(i + 1, len(new_tokens)):
                if new_tokens[j].lower() in list_of_urls:
                    email_string = email_string + new_tokens[j]
                    break;
                else:
                    if (new_tokens[j] == "DOT"):
                        email_string = email_string + '.'
                    else:
                        email_string = email_string + new_tokens[j]
            if (len(email_string) < 35):
                emaillist.append(email_string)
    pattern = r"(^ *[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    email_list = []
    # an extra level of check where each email address extracted is comapared with the regular expressions to prevent false positives being selected as email addressed(could result from non trivial extraction(2)
    for email in emaillist:
        if re.search(pattern, email):
            if email[0] == ' ':
                email = email.split(' ')[1]
            email_list.append(email)
    # write the downloaded link into a file
    email_list=[e.lower() for e in email_list]
    os.system('rm doc_final.pdf')
    os.system('rm doc_final.txt')
    return email_list


def get_emails(paper_name):
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': 'eac6a9fae115422281d64a566bac84d7',
    }

    stripPunctuation = r'[^A-zÀ-ÿ\d\s]'
    # paper_name='On the Difficulty of Training Recurrent Neural Networks'
    normalized_paper_name = (re.sub(stripPunctuation, ' ', paper_name)).lower()
    stripExtraSpaces = r'[ ]+'
    normalized_paper_name = re.sub(stripExtraSpaces, ' ', normalized_paper_name)

    # add the parameters to the http request
    params = urllib.parse.urlencode({
        # Request parameters
        # 'expr': 'Ti=\'on the difficulty of training recurrent neural networks\'',
        'expr': 'Ti=\'' + normalized_paper_name + '\'',
        'model': 'latest',
        'count': '10',
        'offset': '0',
        # 'orderby': '{string}',
        'attributes': 'Ti,Id,AA.AuN,E',
    })

    try:
        # set up a connection to Microsoft Academic Graph (MAG) REST Endpoint
        conn = http.client.HTTPSConnection('westus.api.cognitive.microsoft.com')
        # send http request
        conn.request("GET", "/academic/v1.0/evaluate?%s" % params, "{body}", headers)
        # get response
        response = conn.getresponse()
        data = response.read()
        conn.close()
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

    # metadata response is an array of bytes, needs to be converted to a string
    metadata_str = data.decode('utf-8')

    # metadata dictionary is encoded as String, converted into a Python dict
    metadata_dict = json.loads(metadata_str)

    # extract dict of extended metadata (present as String) from metadata
    try:
        extended_metadata_dict = json.loads(metadata_dict['entities'][0]['E'])
    except Exception as e:
        print("Couldn't find paper on MAG")
        return
    web_resources = extended_metadata_dict['S']

    pdf_link_present = 0
    # identify and extract pdf links from web data
    for item in web_resources:
        if item['Ty'] == 3:
            pdf_link_present += 1
            pdf_url = item['U']
            #print("The url is", pdf_url)
            pdf_text = get_pdf_contents(pdf_url)
            emails = get_emails_from_text(pdf_text)
            print("The extracted emails are:", emails)

    if(pdf_link_present==0):
        print("No link available")

paper_name = input("Enter the name of the paper for which you want email addresses:\n")
get_emails(paper_name)

