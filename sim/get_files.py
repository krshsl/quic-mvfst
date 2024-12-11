from os import path, mkdir, remove
from subprocess import run

class SIM_FILES:
    def __init__(self): # storing everything inside index.html
        self.sim_dir = path.dirname(path.realpath(__file__))
        self.download_init_file("index.html", "www.google.com", self.google_parser_rule)
        self.download_init_file("index.html", "www.example.org", self.example_parser_rule)
        self.download_init_file("index.html", "demo.borland.com/testsite/stadyn_largepagewithimages.html", self.demo_parser_rule)

    def example_parser_rule(self, content, sim_url):
        old_line = "Content-Length: 1256"
        new_line = 'Content-Length: 1304\nX-Original-Url: https://%s/\n' % sim_url
        return content.replace(old_line, new_line)

    def google_parser_rule(self, content, sim_url):
        old_line = "Transfer-Encoding: chunked"
        new_line = 'X-Original-Url: https://%s/\n' % sim_url
        return content.replace(old_line, new_line)

    def demo_parser_rule(self, content, sim_url):
        old_line = "Content-Length: 239012\n"
        new_line = "Content-Length: 239029\nX-Original-Url: https://%s/\n" % sim_url
        return content.replace(old_line, new_line)

    def download_init_file(self, sim_file, sim_url, parser_rule):
        temp_file = path.join(self.sim_dir, sim_file)
        run(['wget', '-q', '-O', '%s'%temp_file, '--save-headers', '%s'%sim_url])

        sim_url = sim_url.split("/")[0] # website name is sufficient
        sim_url_dir = path.join(self.sim_dir, sim_url)
        if not path.exists(sim_url_dir):
            mkdir(path.join(self.sim_dir, sim_url))

        sim_file = path.join(sim_url_dir, sim_file)
        try:
            with open(temp_file, "r", encoding="utf-8") as file:
                content = file.read()
        except UnicodeDecodeError:
            with open(temp_file, "r", encoding="iso-8859-1") as file:
                content = file.read()

        content = parser_rule(content, sim_url)

        with open(sim_file, 'w', encoding="utf-8") as file:
            file.write(content)

        remove(temp_file)
        print(sim_url_dir, sim_file, "%s kb"%(path.getsize(sim_file)/1024))

if __name__ == "__main__":
    SIM_FILES()
