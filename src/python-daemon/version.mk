NAME               = python-daemon
VERSION            = 1.5.5
RELEASE            = 1
PKGROOT            = `python -c 'import sys; print sys.path[-1]'`/daemon

SRC_SUBDIR         = python-daemon

SOURCE_NAME        = $(NAME)
SOURCE_VERSION     = $(VERSION)
SOURCE_SUFFIX      = tar.gz
SOURCE_PKG         = $(SOURCE_NAME)-$(SOURCE_VERSION).$(SOURCE_SUFFIX)
SOURCE_DIR         = $(SOURCE_PKG:%.$(SOURCE_SUFFIX)=%)

TAR_GZ_PKGS        = $(SOURCE_PKG)
