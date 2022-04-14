import argparse
from curses import newpad
import os.path
import re


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('-d', '--directory', required=True, help='Directory to rename files in')
    ap.add_argument('-n', '--newname', required=True, help='Autoincrementing name for files; use %%n to replace with the incrementing number (e.g. "file%%n"). If a regex pattern is used, @n, can be used to substitute groups. @0 for the entire match, and then group numbers starting at 1. Existing extensions will be preserved')
    ap.add_argument('-x', '--extension', help='Change all file extensions to this extension. If not provided, use existing extension')
    ap.add_argument('-r', '--regex', help='Regex pattern to match files against. Only files matching the pattern will be renamed.')
    return ap.parse_args()


def normalize_path(path):
    return os.path.abspath(os.path.expanduser(path))


def split(filename):
    *names, last = filename.rsplit('.')
    return '.'.join(names), last


def check_name(name, illegal='/\\:*?"<>|%$()!@#%^&*()_+{}[];<>'):
    if any(c in name for c in illegal):
        raise ValueError('Illegal character in name: {}'.format(name))


def check_exists(original_path, new_path):
    if os.path.exists(new_path):
        while True:
            response = input("File already exists. Overwrite? ([y]es/[n]o/[q]uit) ")
            if response.strip().lower() == 'y':
                os.rename(original_path, new_path)
                print('Renamed {} to {}'.format(original_path, new_path))
                break
            elif response.strip().lower() == 'n':
                print('Skipped {}'.format(original_path))
                break
            elif response.strip().lower() == 'q':
                print('Quit')
                return -1
            else:
                print('Invalid response: {}'.format(response))
    else:
        os.rename(original_path, new_path)
        print('Renamed {} to {}'.format(original_path, new_path))
    return 0


class FileMatch:
    def __init__(self, filename, match):
        self.filename = filename
        self.match = match

    def is_regex(self):
        return isinstance(self.match, re.Pattern)

    def groups(self):
        if self.is_regex():
            return self.match.groups()
        else:
            return tuple()

    def group(self, n):
        if self.is_regex():
            return self.match.group(n)
        else:
            return self.filename if n == 0 else []


def process_extension(ext, new_ext):
    if new_ext:
        if new_ext.startswith('.'):
            new_ext = new_ext[1:]
        return new_ext
    else:
        return ext


def add_name_numbers(name_template, index):
    if name_template.find('%n') == -1:
        new_name = name_template + '%n'
    else:
        new_name = name_template
    return new_name.replace('%n', str(index))


def format_regex_groups(name_format, match):
    count = 0
    groups = (match.group(0),) + match.groups()
    for match in groups:
        name_format = name_format.replace('@' + str(count), match)
        count += 1
    return name_format


def get_target_files(directory, regex):
    content = os.listdir(directory)
    if regex:
        pattern = re.compile(regex)
        c = []
        for f in content:
            p = pattern.match(f)
            if p:
                c.append(FileMatch(f, p))
        content = c
    else:
        content = [FileMatch(f, None) for f in content]
    return content


def main():
    args = parse_args()
    args.directory = normalize_path(args.directory)

    if not os.path.isdir(args.directory):
        raise ValueError('Directory does not exist: {}'.format(args.directory))

    content = get_target_files(args.directory, args.regex)

    index = 1
    for obj in content:
        original = obj.filename
        name, ext = split(obj.filename)
        ext = process_extension(ext, args.extension)
        new_name = add_name_numbers(args.newname, index)
        new_name = new_name.replace('%n', str(index)) + '.' + ext
        try:
            new_name = format_regex_groups(new_name, obj.match)
        except AttributeError:
            if args.regex:
                raise

        if name == new_name:
            print('Skipping {} because name didn\'t change'.format(original))
            continue

        check_name(new_name)

        new_path = os.path.join(args.directory, new_name)
        if check_exists(os.path.join(args.directory, original), new_path):
            return

        index += 1


if __name__ == '__main__':
    main()
