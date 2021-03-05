import os
import tempfile
import textwrap
import unittest
import trashy_rm
from unittest import mock


class TestHarness(unittest.TestCase):
    def test_harness(self):
        app_config = trashy_rm.AppConfig()
        exec_config = trashy_rm.ExecutionConfig()
        self.assertEqual(0, trashy_rm.run(app_config, exec_config))

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

        with tempfile.NamedTemporaryFile('w+') as config1,\
                tempfile.NamedTemporaryFile('w+') as config2,\
                tempfile.NamedTemporaryFile('w+') as config3,\
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


if __name__ == '__main__':
    unittest.main()
