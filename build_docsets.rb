#!/usr/bin/env ruby 

class JavadocArchive 
  attr_accessor :name, :path
  def initialize(name, path)
    @name = name
    @path = path
  end 
end 

target_entries = []
if ARGV.length==0 
  re = Regexp.compile("(?<name>.*?)-(?<version>[0-9\.]+).*?-javadoc\.jar")
  Dir.foreach('.') do |filename| 
    match_data = re.match(filename)
    target_entries << JavadocArchive.new(match_data['name'], filename) if match_data
  end 
else
  name = ARGV[0]
  re = Regexp.new("#{name}.*?-javadoc\.jar")
  Dir.foreach('.') do |filename| 
    target_entries << JavadocArchive.new(name, filename) if filename =~ re
  end
end 

if target_entries.length==0
  puts "Not found any javadoc archives."
  exit(0)
end

target_entries.each do |entry|
  system("mkdir tmp")
  system("cd tmp && jar xf ../#{entry.path}")
  system("javadocset #{entry.name} tmp") # https://github.com/Kapeli/javadocset#readme
  system("rm -rf tmp")
end
