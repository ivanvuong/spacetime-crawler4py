import re
from urllib.parse import urlparse, urldefrag
from lxml import html 
from collections import Counter

STOP_WORDS = {
    "a","about","above","after","again","against","all","am","an","and","any","are","aren't",
    "as","at","be","because","been","before","being","below","between","both","but","by",
    "can't","cannot","could","couldn't","did","didn't","do","does","doesn't","doing","don't",
    "down","during","each","few","for","from","further","had","hadn't","has","hasn't","have",
    "haven't","having","he","he'd","he'll","he's","her","here","here's","hers","herself","him",
    "himself","his","how","how's","i","i'd","i'll","i'm","i've","if","in","into","is","isn't",
    "it","it's","its","itself","let's","me","more","most","mustn't","my","myself","no","nor",
    "not","of","off","on","once","only","or","other","ought","our","ours","ourselves","out",
    "over","own","same","shan't","she","she'd","she'll","she's","should","shouldn't","so",
    "some","such","than","that","that's","the","their","theirs","them","themselves","then",
    "there","there's","these","they","they'd","they'll","they're","they've","this","those",
    "through","to","too","under","until","up","very","was","wasn't","we","we'd","we'll","we're",
    "we've","were","weren't","what","what's","when","when's","where","where's","which","while",
    "who","who's","whom","why","why's","with","won't","would","wouldn't","you","you'd","you'll",
    "you're","you've","your","yours","yourself","yourselves"
}

word_frequencies = Counter()
page_word_counts = {}
unique_visited = set()

def tokenize_string(s):
    tokens = []
    curr = ""
    for ch in s:
        if ch.isascii() and ch.isalnum():
            curr += ch
        else:
            if curr:
                tokens.append(curr.lower())
                curr = ""
    if curr:
        tokens.append(curr.lower())
    return tokens

def count_words(url, resp):
    if resp.status != 200:
        return

    text = getattr(resp.raw_response, "text", "")
    if not text.strip():
        return 

    try:
        page = html.fromstring(text).text_content().lower()
    except Exception:
        return
    
    valid_tokens = []
    tokens = tokenize_string(page)
    for t in tokens:
        if len(t) >= 2 and t.isalpha() and t not in STOP_WORDS:
            valid_tokens.append(t)
            word_frequencies[t] += 1
    
    page_word_counts[url] = len(valid_tokens)

def scraper(url, resp):
    defragmented_link, fragment = urldefrag(url)
    unique_visited.add(defragmented_link)

    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    count_words(url, resp)

    parsed_links = []
    clean_links = [] 

    if resp.status == 200:
        body = resp.raw_response.content or bytes() 
        if resp.raw_response is None or not body.strip():
            return []
        try: 
            content = html.fromstring(body)
            text = content.text_content()
            if len(text.split()) < 100:
                return []
            parsed_links = content.xpath("//a/@href")
        except Exception as e:
            return []
    else:
        print(resp.error)
        return []
    
    for link in parsed_links:
        defragmented_link, fragment = urldefrag(link)
        if (is_valid(defragmented_link)):
            clean_links.append(defragmented_link)
    return clean_links 

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        host = parsed.netloc.lower()
        path = (parsed.path or '/').rstrip('/')
        query = parsed.query.lower()

        if scheme not in set(["http", "https"]):
            return False
      
        allowed_urls = (
           host.endswith(".ics.uci.edu")
           or host.endswith(".cs.uci.edu")
           or host.endswith(".informatics.uci.edu")
           or host.endswith(".stat.uci.edu")
        )

        if not (allowed_urls or (host == "today.uci.edu" and path.startswith("/department/information_computer_sciences/"))):
            return False

        if "login" in path or "login" in query:
            return False

        if "/day/" in path or "ical" in query or "tribe-bar-date" in query:
            return False

        if path.count("/") > 6:
            return False

        if (scheme + "://" + host + path) in unique_visited:
            return False

        if (len(path) > 7):
            end_years = path[-7:]
            if (end_years[0:4].isdigit() and end_years[4] == "-" and end_years[5:].isdigit()):
                year = int(end_years[0:4])
                if year < 2010:
                    return False 

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def print_top_50():
    top_50 = word_frequencies.most_common(50)
    rank = 1
    for word, count in top_50:
        print(rank, word, count)
        rank += 1

def number_of_unique_pages():
    return len(unique_visited)

def longest_page():
    if len(page_word_counts) == 0:
        return
    longest_page_url = None
    max = 0
    for url, i in page_word_counts.items():
        if i > max:
            max = i
            longest_page_url = url
    print("Longest page: ", longest_page_url)

def get_subdomains():
    subdomains = {}
    for url in unique_visited:
        host = urlparse(url).netloc.lower()
        prev = subdomains.get(host)
        if prev is None:
            prev = 0
        subdomains[host] = prev + 1
    return subdomains