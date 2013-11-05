# ant(./build.xml), gradle(./build.gradle), make(./Makefile), setuptools(./setup.py)
function make --description "Detect cwd's well-known build files then execute it"
  if test -f ./Makefile;      command make $argv;     return; end
  if test -f ./build.gradle;  command gradle --daemon $argv; return; end
  if test -f ./build.xml;     command ant $argv;      return; end
  if test -f ./setup.py;      command python setup.py $argv; return; end;
  eval (which make)
end
