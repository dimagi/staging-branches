# staging-branches

`staging-branches` is a repo hosting the branches configuration for [commcare-hq](https://github.com/dimagi/commcare-hq/)'s staging environment

## Workflow

* Add the branch you'd like to deploy to staging to [the yaml file](https://github.com/dimagi/staging-branches/blob/main/commcare-hq-staging.yml) in this repository. You may use the github UI or edit it however you choose.
* Commit your changes directly to master.  Don't worry about a detailed commit message unless you're doing something unusual.
* From the root of the `commcare-hq` repository, run `./scripts/rebuildstaging`.  This will build a branch called `autostaging` that contains all branches specified in this file.
  * To check if your nelwy added branch causes any conflicts before pushing to autostaging, run:
    ```
    $ scripts/rebuildstaging --no-push
    ```
  * To rebuild autostaging and push those changes to origin (necessary for deploy), run:
     ```
     $ scripts/rebuildstaging
     ```
* After rebuilding the autostaging branch, you need to deploy the new branch to staging.
  ```
  $ commcare-cloud --control staging deploy
  ##### OR #####
  $ scripts/rebuildstaging --deploy (NOTE: `commcare-cloud` must be available in your shell)
  ```

## RESOLVING BRANCH CONFLICTS

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


## FORMPLAYER

TODO
