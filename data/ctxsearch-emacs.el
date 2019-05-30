

(setq ctxsearch-pid-forget 60)
(setq ctxsearch-pid 0)
(setq ctxsearch-pid-time 0)

(defun ctxsearch-post-command ()
  (when (> (nth 1 (time-since ctxsearch-pid-time)) ctxsearch-pid-forget)
    (setq ctxsearch-pid (string-to-number 
       (shell-command-to-string (format "ps -u%s | grep %s | cut -c1-6" (getenv "USER") "ctxsearch"))
      ))
    (setq ctxsearch-pid-time (current-time))
    )
  (when ctxsearch-pid
    ;(message "kill!")
    (signal-process ctxsearch-pid 'usr1)
    )
  )

(add-hook 'post-command-hook 'ctxsearch-post-command)
