" This is the main vimscript file for handling vobby

" This is basic vim plugin boilerplate
let s:save_cpo = &cpo
set cpo&vim

augroup vobby
    autocmd!
    " Kill a running server
    " autocmd VimLeave 
augroup END

let s:script_folder_path = escape( expand( '<sfile>:p:h' ), '\' )

py import sys
exe 'python sys.path.insert( 0, "' . s:script_folder_path . '/../python" )'

" Not sure this works??? need to launch in background
exe 'python "' . s:script_folder_path . '/../python/run.py"'


command! VobbyBrowse call vobby#Browse()
command! -nargs=1 VobbyOpen call vobby#open(<args>)
