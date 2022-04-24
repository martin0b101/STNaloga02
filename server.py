"""An example of a simple HTTP server."""
import json
import mimetypes
import pickle
import socket
from os import listdir
from os.path import isdir, isfile, join
from urllib.parse import unquote_plus, urlparse

# Pickle file for storing data
PICKLE_DB = "db.pkl"

# Directory containing www data
WWW_DATA = "www-data"

# Header template for a successful HTTP request
HEADER_RESPONSE_200 = """HTTP/1.1 200 OK\r
content-type: %s\r
content-length: %d\r
connection: Close\r
\r
"""

# Represents a table row that holds user data
TABLE_ROW = """
<tr>
    <td>%d</td>
    <td>%s</td>
    <td>%s</td>
</tr>
"""

RESPONSE405 = """HTTP/1.1 405 Method not allowed\r
content-type: text/html\r
connection: Close\r
\r
<!doctype html>
<h1>405 Method not allowed</h1>
<p>Method is not allowed.</p>
"""


# Template for a 404 (Not found) error
RESPONSE_404 = """HTTP/1.1 404 Not found\r
content-type: text/html\r
connection: Close\r
\r
<!doctype html>
<h1>404 Page not found</h1>
<p>Page cannot be found.</p>
"""



DIRECTORY_LISTING = """<!DOCTYPE html>
<html lang="en">
<meta charset="UTF-8">
<title>Directory listing: %s</title>

<h1>Contents of %s:</h1>

<ul>
{{CONTENTS}}
</ul> 
"""

FILE_TEMPLATE = "  <li><a href='%s'>%s</li>"


def save_to_db(first, last):
    """Create a new user with given first and last name and store it into
    file-based database.

    For instance, save_to_db("Mick", "Jagger"), will create a new user
    "Mick Jagger" and also assign him a unique number.

    Do not modify this method."""

    existing = read_from_db()
    existing.append({
        "number": 1 if len(existing) == 0 else existing[-1]["number"] + 1,
        "first": first,
        "last": last
    })
    with open(PICKLE_DB, "wb") as handle:
        pickle.dump(existing, handle)


def read_from_db(criteria=None):
    """Read entries from the file-based DB subject to provided criteria

    Use this method to get users from the DB. The criteria parameters should
    either be omitted (returns all users) or be a dict that represents a query
    filter. For instance:
    - read_from_db({"number": 1}) will return a list of users with number 1
    - read_from_db({"first": "bob"}) will return a list of users whose first
    name is "bob".

    Do not modify this method."""
    if criteria is None:
        criteria = {}
    else:
        # remove empty criteria values
        for key in ("number", "first", "last"):
            if key in criteria and criteria[key] == "":
                del criteria[key]

        # cast number to int
        if "number" in criteria:
            criteria["number"] = int(criteria["number"])

    try:
        with open(PICKLE_DB, "rb") as handle:
            data = pickle.load(handle)

        filtered = []
        for entry in data:
            predicate = True

            for key, val in criteria.items():
                if val != entry[key]:
                    predicate = False

            if predicate:
                filtered.append(entry)

        return filtered
    except (IOError, EOFError):
        return []



def parse_headers(client):
    headers = dict()
    while True:
        line = client.readline().decode("utf-8").strip()

        if not line:
            return headers

        key, value = line.split(":", 1)
        headers[key.strip()] = value.strip()


# get post parametre
def get_post_parameters(client,headers):
    parametri = client.read(int(headers.get("Content-Length")))
    user = parametri.decode("utf-8")
    user = user.split("&")
    name = user[0].split("=")[1]
    last_name = user[1].split("=")[1]
    #print("User is:", name, " last name: ", last_name)
    return name, last_name


#if get /index.html
def check_if_just_index(uri):
    if uri[1:] == "index.html":
        return "/www-data/index.html"


def process_request(connection, address):
    """Process an incoming socket request.

    :param connection is a socket of the client
    :param address is a 2-tuple (address(str), port(int)) of the client
    """
    wrongMethod = False

    # Read and parse the request line
    client = connection.makefile("wrb")
    clientForDate = client
    # Read and parse headers
    line = client.readline().decode("utf-8").strip()
    try:
        method, uri, version = line.split()

        # check uri
        uri_razclenjen = uri.split("/")
        if len(uri_razclenjen) == 2:
            if isfile('./www-data/'+uri_razclenjen[1]):
                uri = "/www-data/" + uri_razclenjen[1]

        # check if index exist
        if uri[-1] == "/":
            path = uri
            uri = path+"/index.html"

        assert method == "GET" or method == "POST", "Nedela"
        #check if method is get or post

        checkMetod = method.replace(" ", "")
        if str(checkMetod) == "GET" or str(checkMetod) == "POST":
            wrongMethod = False
        else:
            wrongMethod = True

        assert len(uri) > 0 and uri[0] == "/", "Invalid request URI"
        assert version == "HTTP/1.1", "Invalid HTTP version"





        headers = parse_headers(client)

        # vemo da mamo nek parameter
        if "?" in uri:
            # napisi metodo ko ki vrne vrednosti v listu
            print(unquote_plus(urlparse(uri)[4]).split("&"))
        print(method, uri, version, headers)


        # check if last is app-add
        app_add = uri[-7:] == "app-add"
        if app_add:
            uri = uri[:-7] + "app_add.html"

        app_index = uri[-9:] == "app-index"
        if app_index:
            uri = uri[:-9] + "app_list.html"

        # get post parametre
        if method == "POST":
            name, last_name = get_post_parameters(client, headers)


        with open(uri[1:], "rb") as handle:
            body = handle.read()




        head = HEADER_RESPONSE_200 % (
            # "text/html",
            mimetypes.guess_type(uri[1:])[0],
            len(body)
        )
        client.write(head.encode("utf-8"))
        client.write(body)

    except (ValueError, AssertionError) as e:
        print("Invalid request %s (%s)" % (line, e))
    except IOError:
        if wrongMethod:
            client.write(RESPONSE405.encode("utf-8"))
        else:
            client.write(RESPONSE_404.encode("utf-8"))
    finally:
        client.close()

    # Read and parse the body of the request (if applicable)

    # create the response

    # Write the response back to the socket


def main(port):
    """Starts the server and waits for connections."""

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("", port))
    server.listen(1)

    print("Listening on %d" % port)

    while True:
        connection, address = server.accept()
        print("[%s:%d] CONNECTED" % address)
        process_request(connection, address)
        connection.close()
        print("[%s:%d] DISCONNECTED" % address)


if __name__ == "__main__":
    main(8080)
