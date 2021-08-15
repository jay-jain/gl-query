#!/bin/bash
# Ensure that this script is being executed from root of repository
if [[ `pwd | grep -c tests` -eq "1" ]]
then
  echo "Go back one dir! "
  cd ..
fi

CURRENT_VERSION=$(cut -d "=" -f 2 <<< $(cat setup.cfg | grep current_version) | xargs)
echo "CURRENT VERSION is: $CURRENT_VERSION"
if [[ "$CURRENT_VERSION" = "0.0.0" ]]
then
  echo "Setting NEW VERSION to CURRENT_VERSION ! "
  NEW_VERSION=$CURRENT_VERSION
else
  # Bump Patch Version
  bumpversion --current-version $CURRENT_VERSION patch setup.py gl_query/__init__.py --allow-dirty
  NEW_VERSION=$(cut -d "=" -f 2 <<< $(cat setup.cfg | grep current_version) | xargs)
fi
echo "NEW VERSION is: $NEW_VERSION"

# Build
python3 setup.py sdist bdist_wheel

## Create Unique filename for .whl and .tar.gz
HASH=`openssl rand -hex 12 | cut -c1-5`
WHL_FILENAME="gl_query-${NEW_VERSION}${HASH}-py3-none-any.whl"
TAR_FILENAME="gl-query-${NEW_VERSION}-${HASH}.tar.gz"
# Rename file
mv dist/gl_query-${NEW_VERSION}-py3-none-any.whl dist/$WHL_FILENAME
mv dist/gl-query-${NEW_VERSION}.tar.gz dist/$TAR_FILENAME

# Validate
twine check dist/$WHL_FILENAME
twine check dist/$TAR_FILENAME

# Deploy
### You need to make sure TWINE_USERNAME and TWINE_PASSWORD env. variables are set
twine upload --repository-url https://test.pypi.org/legacy/ dist/$WHL_FILENAME --non-interactive
twine upload --repository-url https://test.pypi.org/legacy/ dist/$TAR_FILENAME --non-interactive

pip3 uninstall gl-query -y
until pip3 install -i https://test.pypi.org/simple/ gl-query==${NEW_VERSION}${HASH} --no-cache-dir
do
  echo "Failed. Trying again."
done

gl-query --version

if [[ $? -eq "0" ]]
then
  echo "Deployed to test.pypi.org successfully. Please make sure you have committed your changes if version numbers have been updated."
fi

## Clean up local dist
rm dist/$WHL_FILENAME || true
rm dist/$TAR_FILENAME || true