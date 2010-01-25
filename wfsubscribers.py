# -*- coding: utf-8 -*-
#
# File: wfsubscribers.py
#
# Copyright (c) 2010 by []
# Generator: ArchGenXML Version 2.4.1
#            http://plone.org/products/archgenxml
#
# GNU General Public License (GPL)
#

__author__ = """unknown <unknown>"""
__docformat__ = 'plaintext'


##code-section module-header #fill in your manual code here
##/code-section module-header


def doBackToItemCreated(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['backToItemCreated'] \
       or obj != event.object:
        return
    ##code-section doBackToItemCreated #fill in your manual code here
    ##/code-section doBackToItemCreated


def doBackToPropose(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['backToProposed'] \
       or obj != event.object:
        return
    ##code-section doBackToPropose #fill in your manual code here
    ##/code-section doBackToPropose


def doValidate(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['validate'] \
       or obj != event.object:
        return
    ##code-section doValidate #fill in your manual code here
    ##/code-section doValidate


def doBackToPublished(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['adviceBackToPublished'] \
       or obj != event.object:
        return
    ##code-section doBackToPublished #fill in your manual code here
    ##/code-section doBackToPublished


def doBackToCreated(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['adviceBackToCreated'] \
       or obj != event.object:
        return
    ##code-section doBackToCreated #fill in your manual code here
    ##/code-section doBackToCreated


def doPresent(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['present'] \
       or obj != event.object:
        return
    ##code-section doPresent #fill in your manual code here
    ##/code-section doPresent


def doClose(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['adviceClose'] \
       or obj != event.object:
        return
    ##code-section doClose #fill in your manual code here
    ##/code-section doClose


def doBackToFrozen(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['backToFrozen'] \
       or obj != event.object:
        return
    ##code-section doBackToFrozen #fill in your manual code here
    ##/code-section doBackToFrozen


def doFreeze(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['freeze'] \
       or obj != event.object:
        return
    ##code-section doFreeze #fill in your manual code here
    ##/code-section doFreeze


def doClose(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['close'] \
       or obj != event.object:
        return
    ##code-section doClose #fill in your manual code here
    ##/code-section doClose


def doBackToValidated(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['backToValidated'] \
       or obj != event.object:
        return
    ##code-section doBackToValidated #fill in your manual code here
    ##/code-section doBackToValidated


def doPropose(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['propose'] \
       or obj != event.object:
        return
    ##code-section doPropose #fill in your manual code here
    ##/code-section doPropose


def doArchive(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['archive'] \
       or obj != event.object:
        return
    ##code-section doArchive #fill in your manual code here
    ##/code-section doArchive


def doPublish(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['advicePublish'] \
       or obj != event.object:
        return
    ##code-section doPublish #fill in your manual code here
    ##/code-section doPublish


def doBackToDecided(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['backToDecided'] \
       or obj != event.object:
        return
    ##code-section doBackToDecided #fill in your manual code here
    ##/code-section doBackToDecided


def doBackToPresented(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['backToPresented'] \
       or obj != event.object:
        return
    ##code-section doBackToPresented #fill in your manual code here
    ##/code-section doBackToPresented


def doBackToCreated(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['backToCreated'] \
       or obj != event.object:
        return
    ##code-section doBackToCreated #fill in your manual code here
    ##/code-section doBackToCreated


def doBackToItemFrozen(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['backToItemFrozen'] \
       or obj != event.object:
        return
    ##code-section doBackToItemFrozen #fill in your manual code here
    ##/code-section doBackToItemFrozen


def doBackToRefused(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['backToRefused'] \
       or obj != event.object:
        return
    ##code-section doBackToRefused #fill in your manual code here
    ##/code-section doBackToRefused


def doBackToPublished(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['backToPublished'] \
       or obj != event.object:
        return
    ##code-section doBackToPublished #fill in your manual code here
    ##/code-section doBackToPublished


def doDecide(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['decide'] \
       or obj != event.object:
        return
    ##code-section doDecide #fill in your manual code here
    ##/code-section doDecide


def doItemArchive(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['itemarchive'] \
       or obj != event.object:
        return
    ##code-section doItemArchive #fill in your manual code here
    ##/code-section doItemArchive


def doBackToItemPublished(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['backToItemPublished'] \
       or obj != event.object:
        return
    ##code-section doBackToItemPublished #fill in your manual code here
    ##/code-section doBackToItemPublished


def doRefuse(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['refuse'] \
       or obj != event.object:
        return
    ##code-section doRefuse #fill in your manual code here
    ##/code-section doRefuse


def doPublish(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['publish'] \
       or obj != event.object:
        return
    ##code-section doPublish #fill in your manual code here
    ##/code-section doPublish


def doItemFreeze(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['itemfreeze'] \
       or obj != event.object:
        return
    ##code-section doItemFreeze #fill in your manual code here
    ##/code-section doItemFreeze


def doAccept(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['accept'] \
       or obj != event.object:
        return
    ##code-section doAccept #fill in your manual code here
    ##/code-section doAccept


def doBackToConfirmed(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['backToConfirmed'] \
       or obj != event.object:
        return
    ##code-section doBackToConfirmed #fill in your manual code here
    ##/code-section doBackToConfirmed


def doRepublish(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['republish'] \
       or obj != event.object:
        return
    ##code-section doRepublish #fill in your manual code here
    ##/code-section doRepublish


def doConfirm(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['confirm'] \
       or obj != event.object:
        return
    ##code-section doConfirm #fill in your manual code here
    ##/code-section doConfirm


def doItemPublish(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['itempublish'] \
       or obj != event.object:
        return
    ##code-section doItemPublish #fill in your manual code here
    ##/code-section doItemPublish


def doBackToDelayed(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['backToDelayed'] \
       or obj != event.object:
        return
    ##code-section doBackToDelayed #fill in your manual code here
    ##/code-section doBackToDelayed


def doBackToClosed(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['backToClosed'] \
       or obj != event.object:
        return
    ##code-section doBackToClosed #fill in your manual code here
    ##/code-section doBackToClosed


def doDelay(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['delay'] \
       or obj != event.object:
        return
    ##code-section doDelay #fill in your manual code here
    ##/code-section doDelay


def doBackToAccepted(obj, event):
    """generated workflow subscriber."""
    # do only change the code section inside this function.
    if not event.transition \
       or event.transition.id not in ['backToAccepted'] \
       or obj != event.object:
        return
    ##code-section doBackToAccepted #fill in your manual code here
    ##/code-section doBackToAccepted



##code-section module-footer #fill in your manual code here
##/code-section module-footer

