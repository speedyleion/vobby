" This is the main vimscript file for handling vobby

" This is basic vim plugin boilerplate
let s:save_cpo = &cpo
set cpo&vim

augroup youcompleteme
    autocmd!
    " Kill a running server
    " autocmd VimLeave 
augroup END

let s:script_folder_path = escape( expand( '<sfile>:p:h' ), '\' )

py import sys
exe 'python sys.path.insert( 0, "' . s:script_folder_path . '/../python" )'

" Not sure this works??? need to launchh in background
exe 'python "' . s:script_folder_path . '/../python/run.py"'


" This will open up a window to list the files on the connected infinoted server
" and display their hierarchy.
"
" For now this is hacked to just message out the file names
function! s:VobbyBrowse()
    " Send a message to the vobby server
    :nbkey 'hello'
endfunction
