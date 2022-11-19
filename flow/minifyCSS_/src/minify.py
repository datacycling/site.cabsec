from html.parser import HTMLParser
from pathlib import Path
import sys
import string
import time

LEN_CUTOFF = 1500
IGNORE_STRS_IN_CLASS = ["primary", "search", "expand_text", "group", "hidden", "cursor-pointer"]
JS_CLASSES = [
    "bg-white border border-blue-500 lg:border-r-0 relative text-sm cursor-pointer",
    "p-2 w-full h-full min-w-[210px] relative bg-white focus:bg-white z-20 lg:-right-1 -bottom-4 lg:-bottom-0 text-[#333333]",
    "bg-[#D9D9D9] border border-[#B8B8B8] border-r-0 text-sm text-[#333333] cursor-pointer",
    "p-2 w-full h-full min-w-[210px]",
]

INPUT_HDR ='@tailwind base;\n@tailwind components;\n@tailwind utilities;\n\n'


class ClassRecorder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.class_dict = {}
        self.file_name = None
        self.file_line_num = 0

    def set_file_name(self, file_name):
        self.file_name = file_name
        self.file_line_num = self.getpos()[0]

    def handle_starttag(self, tag, attrs):
        for k, v in ((k, v) for k, v in attrs if k == "class"):
            assert '\n' not in v, f'new line found in class {v}'
            v = v.strip()
            if not v or any(i in v for i in IGNORE_STRS_IN_CLASS + JS_CLASSES):
                continue
            line_num = self.getpos()[1] - self.file_line_num
            self.class_dict.setdefault(v, []).append((self.file_name, line_num))

def get_classes(input_dir):
    class_recorder = ClassRecorder()

    for html_file in input_dir.glob("*.html"):
        class_recorder.set_file_name(html_file.name)
        class_recorder.feed(html_file.read_text())
    class_recorder.close()

    itms = class_recorder.class_dict.items()
    
    return [c for (c, c_lst) in itms if len(c) * len(c_lst) > LEN_CUTOFF]


def write_components(css_path, class_pairs):
    css_components = INPUT_HDR + "@layer components {\n"
    for (long_cls, short_cls) in class_pairs:
        css_components += f"  .{short_cls} {{\n    @apply {long_cls};\n  }}\n"
    css_components += "}"
    css_path.write_text(css_components)


def write_html(input_dir, output_dir, class_pairs):
    for html_file in input_dir.glob("*.html"):
        html_contents = html_file.read_text()
        output_lines = []
        for line in html_contents.split("\n"):
            if "class=" in line:
                for (long, short) in class_pairs:
                    line = line.replace(f'class=" {long}', f'class="{short}')
                    line = line.replace(f'class="{long}', f'class="{short}')
                    line = line.replace(f'class="{long} ', f'class="{short}')                                        
            output_lines.append(line)
        new_file = output_dir / html_file.name
        new_file.write_text("\n".join(output_lines))


if __name__ == "__main__":
    input_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])

    start_time = time.time()
    long_classes = get_classes(input_dir)
    long_classes = JS_CLASSES + long_classes  # ensure JS_CLASSES are at top

    get_classes_time = time.time()
    print(f"--- {get_classes_time - start_time} ---")

    ltrs = string.ascii_letters
    short_classes = [f"{c}-{d}" for c in ltrs[:26] for d in ltrs[:26]]

    assert len(short_classes) > len(long_classes), f'# short names: {len(short_classes)} < {len(long_classes)}'
    class_pairs = sorted(zip(long_classes, short_classes), key=lambda tup: -len(tup[0]))
    
    components_path = output_dir / Path("tailwindcss") / "input_new.css"
    write_components(components_path, class_pairs)

    write_components_time = time.time()
    print(f"--- {write_components_time - get_classes_time} ---")
    

    write_html(input_dir, output_dir, class_pairs)
    
    write_html_time = time.time()
    print(f"--- {write_html_time - write_components_time} ---")
