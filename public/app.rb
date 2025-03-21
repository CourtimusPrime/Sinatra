require 'sinatra'

# Serve the main page
get '/' do
  send_file File.join(settings.public_folder, 'index.html')
end

# Serve the About page
get '/about' do
  send_file File.join(settings.public_folder, 'about.html')
end

# Serve the Contact page
get '/contact' do
  send_file File.join(settings.public_folder, 'contact.html')
end