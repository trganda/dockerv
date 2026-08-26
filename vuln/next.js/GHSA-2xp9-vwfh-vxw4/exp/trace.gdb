set pagination off
set confirm off
set breakpoint pending on
break malloc
commands
silent
if $x0 > 1024
  printf "malloc %lu\n", $x0
end
continue
end
break calloc
commands
silent
if $x0*$x1 > 1024
  printf "calloc %lu\n", $x0*$x1
end
continue
end
run
