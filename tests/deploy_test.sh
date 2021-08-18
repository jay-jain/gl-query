#!/bin/bash
# Ensure that this script is being executed from root of repository
if [[ `pwd | grep -c tests` -eq "1" ]]
then
  echo "Go back one dir! "
  cd ..
fi

CURRENT_VERSION=$(cut -d "=" -f 2 <<< $(cat setup.cfg | grep current_version) | xargs)
echo "CURRENT VERSION is: $CURRENT_VERSION"
echo "Would you like to bump the version up? (WARNING: THIS WILL MODIFY FILES): "
if [[ $input -eq "YES" ]] || [[ $input -eq "yes" ]] || [[ $input -eq "Yes" ]]
then
  echo "BUMPING VERSION..........."
  bumpversion --current-version $CURRENT_VERSION patch setup.py gl_query/__init__.py --allow-dirty
  NEW_VERSION=$(cut -d "=" -f 2 <<< $(cat setup.cfg | grep current_version) | xargs)
  echo "NEW VERSION is: $NEW_VERSION"
fi


upload_hashed(){
  ## Create Unique filename for .whl and .tar.gz
  HASH=`openssl rand -hex 12 | cut -c1-5`
  WHL_FILENAME="gl_query-${1}${HASH}-py3-none-any.whl"
  TAR_FILENAME="gl-query-${1}-${HASH}.tar.gz"
  # Rename file
  mv dist/gl_query-${1}-py3-none-any.whl dist/$WHL_FILENAME
  mv dist/gl-query-${1}.tar.gz dist/$TAR_FILENAME

  # Validate
  twine check dist/$WHL_FILENAME
  twine check dist/$TAR_FILENAME

  # Deploy
  ### You need to make sure TWINE_USERNAME and TWINE_PASSWORD env. variables are set
  twine upload --repository-url https://test.pypi.org/legacy/ dist/$WHL_FILENAME --non-interactive
  twine upload --repository-url https://test.pypi.org/legacy/ dist/$TAR_FILENAME --non-interactive

  cleanup $WHL_FILENAME $TAR_FILENAME
}

upload_normal(){
  WHL_FILENAME=gl_query-${1}-py3-none-any.whl
  TAR_FILENAME=gl-query-${1}.tar.gz
  # Validate
  twine check dist/${WHL_FILENAME}
  twine check dist/${TAR_FILENAME}

  # Deploy
  ### You need to make sure TWINE_USERNAME and TWINE_PASSWORD env. variables are set
  twine upload --repository-url https://test.pypi.org/legacy/ dist/${WHL_FILENAME} --non-interactive
  twine upload --repository-url https://test.pypi.org/legacy/ dist/${TAR_FILENAME} --non-interactive

  cleanup $WHL_FILENAME $TAR_FILENAME
}

smoke_test(){
  pip3 uninstall gl-query -y
  until pip3 install -i https://test.pypi.org/simple/ gl-query==${NEW_VERSION} --no-cache-dir
  do
    echo "Failed. Trying again."
  done

  gl-query --version

  if [[ $? -eq "0" ]]
  then
    echo "Deployed to test.pypi.org successfully. Please make sure you have committed your changes if version numbers have been updated."
  fi
}

cleanup(){
  ## Clean up local dist
  rm dist/${1} || true
  rm dist/${2} || true
}

# Build
python3 setup.py sdist bdist_wheel

# Upload
upload_normal "$NEW_VERSION"

# Smoke test
smoke_test "$NEW_VERSION"