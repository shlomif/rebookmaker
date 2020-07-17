package Shlomif::Screenplays::EPUB;

use strict;
use warnings;

use Carp ();
use Path::Tiny qw/ path /;

use utf8;

use MooX qw/late/;

use XML::LibXML               ();
use XML::LibXML::XPathContext ();

use JSON::MaybeXS qw( encode_json );

use HTML::Widgets::NavMenu::EscapeHtml qw(escape_html);

use Getopt::Long qw(GetOptions);

use File::Copy qw(copy);

has [ 'filename', 'gfx', 'out_fn', 'epub_basename' ] =>
    ( is => 'rw', isa => 'Str' );
has script_dir =>
    ( is => 'ro', default => sub { return path($0)->parent(2)->absolute; } );

has [ 'target_dir', ] => ( is => 'rw' );
has 'images' => ( is => 'ro', isa => 'HashRef[Str]', default => sub { +{}; }, );

has 'common_json_data' => (
    isa       => 'HashRef',
    is        => 'ro',
    'default' => sub {
        return +{
            contents => [
                {
                    "type"   => "toc",
                    "source" => "toc.html"
                },
                {
                    type   => 'text',
                    source => "scene-*.xhtml",
                },
            ],
            toc => {
                "depth"    => 2,
                "parse"    => [ "text", ],
                "generate" => {
                    "title" => "Index"
                },
            },
            guide => [
                {
                    type  => "toc",
                    title => "Index",
                    href  => "toc.html",
                },
            ],
        };
    },
);

use Inline Python => <<'EOF';

def _my_amend_epub(filename):
    from zipfile import ZipFile, ZIP_STORED
    z = ZipFile(filename.decode("utf-8"), 'a')
    z.writestr("mimetype", "application/epub+zip", ZIP_STORED)
    z.close()

EOF

sub json_filename
{
    my ($self) = @_;

    return $self->epub_basename . '.json';
}

my $xhtml_ns = "http://www.w3.org/1999/xhtml";

sub _get_xpc
{
    my ($node) = @_;
    my $xpc = XML::LibXML::XPathContext->new($node);
    $xpc->registerNs( "xhtml", $xhtml_ns );

    return $xpc;
}

sub run
{
    my ($self) = @_;

    my $out_fn;

    GetOptions( "output|o=s" => \$out_fn, )
        or Carp::confess("GetOptions failed - $!");

    $self->out_fn($out_fn);

    # Input the filename
    my $filename = shift(@ARGV)
        or die "Give me a filename as a command argument: myscript FILENAME";

    $self->filename($filename);

    my $target_dir = Path::Tiny->tempdir;
    $self->target_dir($target_dir);

    # Prepare the objects.
    my $xml       = XML::LibXML->new;
    my $root_node = $xml->parse_file($filename);
    {
        my $scenes_list =
            _get_xpc($root_node)
            ->findnodes(
q{//xhtml:main[@class='screenplay']/xhtml:section[@class='scene']/xhtml:section[@class='scene' and xhtml:header/xhtml:h2]}
            ) or die "Cannot find top-level scenes list.";

        my $idx = 0;
        $scenes_list->foreach(
            sub {
                my ($orig_scene) = @_;

                my $scene = $orig_scene->cloneNode(1);

                {
                    my $scene_xpc = _get_xpc($scene);
                    foreach my $h_idx ( 2 .. 6 )
                    {
                        foreach my $h_tag (
                            $scene_xpc->findnodes(
                                qq{descendant::xhtml:h$h_idx})
                            )
                        {
                            my $copy = $h_tag->cloneNode(1);
                            $copy->setNodeName( 'h' . ( $h_idx - 1 ) );

                            my $parent = $h_tag->parentNode;
                            $parent->replaceChild( $copy, $h_tag );
                        }
                    }
                }

                {
                    my $scene_xpc = _get_xpc($scene);

                    my $title =
                        $scene_xpc->findnodes('descendant::xhtml:h1')->[0]
                        ->textContent();
                    my $esc_title = escape_html($title);

                    my $scene_string = $scene->toString();
                    my $xmlns =
q# xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"#;
                    $scene_string =~ s{(<\w+)\Q$xmlns\E( )}{$1$2}g;

                    path(     $target_dir
                            . "/scene-"
                            . sprintf( "%.4d", ( $idx + 1 ) )
                            . ".xhtml" )->spew_utf8(<<"EOF");
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
    path("$target_dir/images")->mkpath;
    my $script_dir = $self->script_dir;
    copy( "$script_dir/../graphics/$gfx", "$target_dir/images/$gfx" );

    my $images = $self->images;
    foreach my $img_src ( keys(%$images) )
    {
        my $dest = "$target_dir/$images->{$img_src}";

        path($dest)->parent->mkpath;
        copy( "$script_dir/../graphics/$img_src", $dest );
    }

    foreach my $basename ('style.css')
    {
        path("$target_dir/$basename")->spew_utf8(<<'EOF');
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

sub output_json
{
    my ( $self, $args ) = @_;

    my $data_tree = $args->{data};

    my $orig_dir = Path::Tiny->cwd->absolute;

    my $target_dir = $self->target_dir;

    my $epub_fn =
        $target_dir->child( path( $self->epub_basename )->basename() . ".epub" )
        ->absolute;

    my $json_filename = $self->json_filename;
    my $json_abs =
        $target_dir->child( path($json_filename)->basename )->absolute;

    $json_abs->spew_utf8(
        encode_json( { %{ $self->common_json_data() }, %$data_tree }, ),
    );

    {
        chdir($target_dir);

        my @cmd = (
            ( $ENV{EBOOKMAKER} || "./lib/ebookmaker/ebookmaker" ),
            "--output", $epub_fn, $json_abs,
        );
        system(@cmd)
            and die "cannot run ebookmaker <<@cmd>> - $!";
        _my_amend_epub( $epub_fn->stringify() );

        chdir($orig_dir);
    }

    $epub_fn->copy( $self->out_fn );

    return;
}

1;

