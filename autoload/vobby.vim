" Vobby autoload script  

" Open a shared infinoted buffer.
" Parameters:
"       file (str): The file to open in the buffer
"
" Like all of the vobby calls to the server this needs to be done through a
" valid infinoted shared buffer.  Usually the `__vobby__` buffer can be used.
function! vobby#Open(file) abort

    " TODO add some error checking.
    " For now just send the message raw and hope we're in a vobby buffer
    exe 'nbkey vobby open ' . file

endfunction

" This will open up a window to list the files on the connected infinoted server
" and display their hierarchy.
function! vobby#Browse()
    " Send a message to the vobby server
    exe 'nbkey vobby hello'
endfunction
