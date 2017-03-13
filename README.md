# fileuploader

The fileuploader contains two URIs:

    /upload - POST (pass Content-Type in headers):
       - Returns a token corresponding to a file

    /token/<token> - GET call:
       - Can redirect to a S3 pre-signed url.
       - If not uploaded or still in process, it will return a message.
       - If upload failed will return with a message


Requirements:

    python 2.7/3.0+

    install using
        ```
        pip install -r requirements.txt
        ```

Test cases are in:
     tests/

    ``` cd tests

        sh tests.sh

    ```

Notes:

Currently using MongoDB to save about token generated and also store status like
    -if file is uploaded(or in process)
    -if upload_failed

This is written using tornado=4.2.

Currently ThreadPool is used to run different uploads on seperate threads, instead of
processes. Threads have the GIL issue on the other hand, processes are not preferred
because multiple uploads will spawn multiple processes.

Good way is to implement a Task Queue processor like Celery
