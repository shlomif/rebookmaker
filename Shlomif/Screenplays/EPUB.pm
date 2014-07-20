package Shlomif::Screenplays::EPUB;

use strict;
use warnings;

use IO::All;

use utf8;

use MooX qw/late/;

use XML::LibXML;
use XML::LibXML::XPathContext;

use CGI qw(escapeHTML);

use Getopt::Long qw(GetOptions);

has ['filename', 'target_dir', 'gfx', 'out_fn', ] => (is => 'rw', isa => 'Str');

my $xhtml_ns = "http://www.w3.org/1999/xhtml";

sub _get_xpc
{
    my ($node) = @_;
    my $xpc = XML::LibXML::XPathContext->new($node);
    $xpc->registerNs("xhtml", $xhtml_ns);

    return $xpc;
}

sub run
{
    my ($self) = @_;

    my $out_fn;

    GetOptions(
        "output|o=s" => \$out_fn,
    );

    $self->out_fn($out_fn);

    # Input the filename
    my $filename = shift(@ARGV)
        or die "Give me a filename as a command argument: myscript FILENAME";

    $self->filename($filename);

    my $target_dir = './for-epub-xhtmls/';
    $self->target_dir($target_dir);

    # Prepare the objects.
    my $xml = XML::LibXML->new;
    my $root_node = $xml->parse_file($filename);
    {
        my $scenes_list = _get_xpc($root_node)->findnodes(
            q{//xhtml:div[@class='screenplay']/xhtml:div[@class='scene']/xhtml:div[@class='scene' and xhtml:h2]}
        )
            or die "Cannot find top-level scenes list.";

        my $idx = 0;
        $scenes_list->foreach(sub
            {
                my ($orig_scene) = @_;

                # Commented out traces. No longer needed.
                # print "\n\n[$idx]<<<<< " . $orig_scene->toString() . ">>>>\n\n";
                # print "Foo ==" , (scalar($orig_scene->toString()) =~ /h3/g), "\n";

                my $scene = $orig_scene->cloneNode(1);

                {
                    my $scene_xpc = _get_xpc($scene);
                    foreach my $h_idx (2 .. 6)
                    {
                        foreach my $h_tag ($scene_xpc->findnodes(qq{descendant::xhtml:h$h_idx}))
                        {
                            my $copy = $h_tag->cloneNode(1);
                            $copy->setNodeName('h' . ($h_idx-1));

                            my $parent = $h_tag->parentNode;
                            $parent->replaceChild($copy, $h_tag);
                        }
                    }
                }

                {
                    my $scene_xpc = _get_xpc($scene);

                    my $title = $scene_xpc->findnodes('descendant::xhtml:h1')->[0]->textContent();
                    my $esc_title = escapeHTML($title);

                    my $scene_string = $scene->toString();
                    my $xmlns = q# xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"#;
                    $scene_string =~ s{(<\w+)\Q$xmlns\E( )}{$1$2}g;

                    io->file($target_dir . "/scene-" . sprintf("%.4d", ($idx+1)) . ".xhtml")->utf8->print(<<"EOF");
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE
    html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
    "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en-US">
<head>
<title>$esc_title</title>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<link rel="stylesheet" href="style.css" />
</head>
<body>
$scene_string
</body>
</html>
EOF
                }
                $idx++;
            }
        );
    }

    my $gfx = 'Green-d10-dice.png';
    $self->gfx($gfx);
    io->file($target_dir . "/images/$gfx")->print(
        io->file('../graphics/' . $gfx)->all
    );

foreach my $basename ('style.css')
{
    io->file( "$target_dir/$basename" )->utf8->print(<<'EOF');
body
{
    direction: ltr;
    text-align: left;
    font-family: sans-serif;
    background-color: white;
    color: black;
}
EOF
}

    return;
}

1;

