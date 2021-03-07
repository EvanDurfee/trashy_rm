import io
import os
import tempfile
import textwrap
import unittest
import trashy_rm
from unittest import mock


class TestOptsParser(unittest.TestCase):
    def assertOptsEqual(self, expected: trashy_rm.ExecConfig, actual: trashy_rm.ExecConfig):
        self.assertEqual(expected.force, actual.force)
        self.assertEqual(expected.handle_dirs, actual.handle_dirs)
        self.assertEqual(expected.recursive, actual.recursive)
        self.assertEqual(expected.interactive_mode, actual.interactive_mode)
        self.assertEqual(expected.verbose, actual.verbose)
        self.assertEqual(expected.help, actual.help)
        self.assertEqual(expected.get_trash, actual.get_trash)
        self.assertEqual(expected.trash_mode, actual.trash_mode)
        self.assertEqual(expected.shred, actual.shred)
        self.assertCountEqual(expected.targets, actual.targets)

    def test_opts1(self):
        expected = trashy_rm.ExecConfig()
        expected.recursive = True
        expected.trash_mode = trashy_rm.TrashMode.ALWAYS
        expected.interactive_mode = trashy_rm.InteractiveMode.ALWAYS
        expected.verbose = True
        expected.handle_dirs = True
        expected.read_targets = True
        expected.targets = ['target1', '/dir/there/target2', '-target3', '--help']
        opts = [
            '--recursive',
            '--recycle',
            '--interactive=always',
            'target1',
            '/dir/there/target2',
            '-vd',
            '-',
            '--',
            '-target3',
            '--help'
        ]
        actual = trashy_rm.parse_opts(opts)
        self.assertOptsEqual(expected, actual)

    def test_opts2(self):
        expected = trashy_rm.ExecConfig()
        expected.interactive_mode = trashy_rm.InteractiveMode.NEVER
        expected.force = True
        expected.help = True
        opts = [
            '--interactive=never',
            '--force',
            '-fh-'
        ]
        actual = trashy_rm.parse_opts(opts)
        self.assertOptsEqual(expected, actual)

    def test_bad_opts1(self):
        # Unrecognized short option '-'
        opts = [
            '-r-d'
        ]
        self.assertRaises(trashy_rm.OptParseError, lambda: trashy_rm.parse_opts(opts))

    def test_bad_opts2(self):
        # Unsupported interactive mode
        opts = [
            '--dry-run,'
            '--interactive=squirrels'
        ]
        self.assertRaises(trashy_rm.OptParseError, lambda: trashy_rm.parse_opts(opts))
        self.assertRaises(trashy_rm.OptParseError, lambda: trashy_rm.parse_opts(opts[::-1]))

    def test_bad_opts3(self):
        # generic unsupported arguments
        opts = [
            '--what',
            '-w'
        ]
        self.assertRaises(trashy_rm.OptParseError, lambda: trashy_rm.parse_opts(opts))
        self.assertRaises(trashy_rm.OptParseError, lambda: trashy_rm.parse_opts(opts[::-1]))


class TestConfig(unittest.TestCase):
    @mock.patch.dict(os.environ, {'HOME': '/tmp/trashy/my$PWD',
                                  'MY_DIR': '/tmp/trashy/test',
                                  'SPACES_DIR': '/tmp/trashy/spa ces'})
    def test_load_config(self):
        # One file with everything
        file1_str = """
           [prompt]
           cutoff = 9
           [trash_path]
           home = /dev/null
           unset = $UNSET/tmp/stuff
           """
        # One file overriding some sections
        file2_str = """
           [trash_path]
           home = ~
           lovelydir = $MY_DIR/directory
           spacesdir = ${SPACES_DIR}-here/dir
           """
        # One file overriding others
        file3_str = """
           [prompt]
           cutoff = 5
           """
        # And one empty file

        with tempfile.NamedTemporaryFile('w+') as config1, \
                tempfile.NamedTemporaryFile('w+') as config2, \
                tempfile.NamedTemporaryFile('w+') as config3, \
                tempfile.NamedTemporaryFile('w+') as config4:
            config1.write(textwrap.dedent(file1_str))
            config2.write(textwrap.dedent(file2_str))
            config3.write(textwrap.dedent(file3_str))
            config_files = [config1, config2, config3, config4]
            for f in config_files:
                f.flush()
            config = trashy_rm.load_app_config([f.name for f in config_files])
            # config = trashy_rm.load_app_config([config1.name])
            self.assertEqual(5, config.cutoff)
            # Ensure we can handle a home dir with a $ in the name
            expected_dirs = ['/tmp/trashy/my$PWD',
                             '/tmp/trashy/test/directory',
                             '/tmp/trashy/spa ces-here/dir',
                             '$UNSET/tmp/stuff']
            self.assertCountEqual(expected_dirs, config.trashy_dirs)


class TestHarness(unittest.TestCase):
    def test_help(self):
        sys_info = trashy_rm.get_system_info()
        app_config = trashy_rm.AppConfig()
        exec_config = trashy_rm.ExecConfig()
        exec_config.force = True
        exec_config.shred = True
        exec_config.verbose = True
        exec_config.help = True
        inp = io.StringIO()
        out = io.StringIO()
        err = io.StringIO()
        self.assertEqual(0, trashy_rm.run(sys_info, app_config, exec_config, inp, out, err))
        self.assertEqual(trashy_rm.__doc__, out.getvalue())
        self.assertEqual('', err.getvalue())


if __name__ == '__main__':
    unittest.main()
