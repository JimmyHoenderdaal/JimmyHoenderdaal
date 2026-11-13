import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('activity', Path(__file__).with_name('update-activity.py'))
activity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(activity)


class ActivityTests(unittest.TestCase):
    def setUp(self):
        self.readme = 'Intro\n<!-- ACTIVITY:START -->\nold\n<!-- ACTIVITY:END -->\nFooter\n'

    def pull(self, repository='rapidez/core', title='A change'):
        return {'repository': {'nameWithOwner': repository}, 'title': title,
                'url': f'https://github.com/{repository}/pull/1'}

    def test_preserves_content_and_is_idempotent(self):
        pulls = [self.pull()]
        result = activity.update_readme(self.readme, pulls, 'JimmyHoenderdaal')
        self.assertTrue(result.startswith('Intro\n'))
        self.assertTrue(result.endswith('\nFooter\n'))
        self.assertNotIn('\nold\n', result)
        self.assertEqual(result, activity.update_readme(result, pulls, 'JimmyHoenderdaal'))

    def test_excludes_own_repositories_and_limits_to_five(self):
        pulls = [self.pull('jimmyhoenderdaal/profile')] + [self.pull(title=f'Change {i}') for i in range(8)]
        result = activity.update_readme(self.readme, pulls, 'JimmyHoenderdaal')
        self.assertNotIn('jimmyhoenderdaal/profile', result)
        self.assertEqual(result.count('- ['), 5)

    def test_escapes_titles(self):
        result = activity.update_readme(self.readme, [self.pull(title='Fix [x] <img>\n*bold*')], 'Jimmy')
        self.assertIn(r'Fix \[x\] &lt;img&gt; \*bold\*', result)

    def test_empty_results(self):
        self.assertIn('No public merged contributions yet.', activity.update_readme(self.readme, [], 'Jimmy'))

    def test_deduplicates_matching_titles_in_the_same_repository(self):
        result = activity.update_readme(self.readme, [self.pull(), self.pull()], 'Jimmy')
        self.assertEqual(result.count('- ['), 1)

    def test_rejects_missing_duplicate_or_reversed_markers(self):
        for readme in ['Intro', self.readme + activity.START, activity.END + activity.START]:
            with self.subTest(readme=readme), self.assertRaises(ValueError):
                activity.update_readme(readme, [], 'Jimmy')


if __name__ == '__main__':
    unittest.main()
