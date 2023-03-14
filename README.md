# staging-branches

`staging-branches` is a repo hosting the branches configuration for [commcare-hq](https://github.com/dimagi/commcare-hq/)'s and [formplayer](https://github.com/dimagi/formplayer)'s staging environments.

## Workflow

The general workflow is virtually the same across repositories. The convention is for a script named `rebuildstaging` to live in the project's `scripts` directory (e.g., `commcare-hq/scripts/rebuildstaging`) which is responsible for fetching the appropriate file from this repository, and building a branch to deploy to the staging environment. 

* Add the branch you'd like to deploy to the appropriate staging configuration file in this repository. The easiest approach is to use the GitHub UI for editing the file directly, but you can choose to edit locally if so desired.
* Commit your changes directly to main.  Don't worry about a detailed commit message unless you're doing something unusual.
* From the root of the repository you want to deploy (e.g., commcare-hq, formplayer, etc), run `./scripts/rebuildstaging`.  This will build a branch called `autostaging` that contains all branches specified in this file.
  * To check if your newly added branch causes any conflicts before pushing to autostaging, run:
    ```
    $ scripts/rebuildstaging --no-push
    ```
* After rebuilding the autostaging branch, you need to deploy the new branch to staging.
  ```
  $ commcare-cloud --control staging deploy
  ##### OR #####
  $ scripts/rebuildstaging --deploy (NOTE: `commcare-cloud` must be available in your shell)
  ```

## Resolving Branch Conflicts

First, determine where the conflict lies.  All of these steps should be taken from the root of the repository you're working on (eg, `commcare-hq`)

#### Branch `foo` conflicts with `master`

```
$ git checkout -b foo origin/foo
$ git pull origin master
```
try to resolve conflict
```
$ git push origin foo
```

#### Branch `foo` conflicts with branch `bar`

You can't just merge foo into bar or vice versa, otherwise the PR
for foo will contain commits from bar.  Instead make a third,
conflict-resolution branch:
```
$ git checkout -b foo+bar --no-track origin/foo
$ git pull origin bar
```
try to resolve conflict
```
$ git push origin foo+bar
```
add the branch `foo+bar` to staging.yml and move branches foo and
bar to right below it:
```
- foo+bar
- foo
- bar
```

Later on branch `bar` gets merged into master and removed from staging.yml.
Perhaps the person who removes it also notices the `foo+bar` and does the
following. Otherwise anyone who comes along and sees `foo+bar` but not both
branches can feel free to assume the following needs to be done:
  * Merge `foo+bar` into `foo`. Since `bar` is now merged and deleted,
    you want to merge the resolution into `foo`, otherwise `foo` will conflict
    with master.
  * Remove `foo+bar` from staging.yml. It's no longer necessary since it's
    now a subset of `foo`.

If you are unsure of how to resolve a conflict, notify the branch owner.
