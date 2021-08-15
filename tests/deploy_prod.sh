#!/bin/bash

#!/bin/bash
# Ensure that this script is being executed from root of repository
if [[ `pwd | grep -c tests` -eq "1" ]]
then
  echo "Go back one dir! "
  cd ..
fi

CURRENT_VERSION=$(cut -d "=" -f 2 <<< $(cat setup.cfg | grep current_version) | xargs)
echo "CURRENT VERSION is: $CURRENT_VERSION"
# Bump Patch Version
bumpversion --current-version $CURRENT_VERSION patch setup.py gl_query/__init__.py --allow-dirty
NEW_VERSION=$(cut -d "=" -f 2 <<< $(cat setup.cfg | grep current_version) | xargs)
echo "NEW VERSION is: $NEW_VERSION"


# Build
python3 setup.py sdist bdist_wheel

# Validate
twine check dist/gl_query-$NEW_VERSION*
twine check dist/gl-query-$NEW_VERSION*

# Deploy
printf "Are YOU 100%% SURE you would like to deploy the new version of gl-query ( $NEW_VERSION ) to PRODUCTION?\n\
This could break downstream customers of this tool ( YES or NO ) ?\n"
read input
if [[ $input -eq "YES" ]] || [[ $input -eq "yes" ]] || [[ $input -eq "Yes" ]]
then
    # You need to make sure TWINE_USERNAME and TWINE_PASSWORD env. variables are set
    twine upload --repository-url https://test.pypi.org/legacy/ dist/gl_query-$NEW_VERSION* --non-interactive
    twine upload --repository-url https://test.pypi.org/legacy/ dist/gl-query-$NEW_VERSION* --non-interactive
fi

pip3 uninstall gl-query -y
until pip3 install -i https://test.pypi.org/simple/ gl-query==$NEW_VERSION --no-cache-dir
do
  echo "Failed. Trying again."
done

gl-query --version