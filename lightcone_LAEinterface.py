#!/usr/bin/env python
# coding: utf-8

#This code takes in an arbitrary set of boxes, whose directory and redshift ranges you must provide, and makes a lightcone
import numpy as np
import matplotlib.pyplot as pl
import sys
import os
import astropy
from astropy.cosmology import Planck15 as p15
from astropy.cosmology import z_at_value
from astropy.cosmology import WMAP9 as cosmo


def lightcone(**kwargs ):

    #set defaults:
    mode = 'xH'
    marker = 'xH_z'
    N = 500
    DIM = 200
    Box_length = 300
    z_start = 6
    z_end = 10
    nboxes = 21
    directory = '/Users/michael/Documents/MSI-C/21cmFAST/Boxes/z6-10/OriginalTemperatureBoxesNoGaussianities/'
    halo_location_x = 0
    halo_location_y = 0

    #sort arguments
    if 'marker' in kwargs:
        marker = kwargs.get('marker')
    if 'DIM' in kwargs:
        DIM = kwargs.get('DIM')
    if 'N' in kwargs:
        N = kwargs.get('N')
    if 'Box_length' in kwargs:
        Box_length = kwargs.get('Box_length')
    if 'z_start' in kwargs:
        z_start = kwargs.get('z_start')
    if 'z_end' in kwargs:
        z_end = kwargs.get('z_end')
    if 'nboxes' in kwargs:
        nboxes = kwargs.get('nboxes')
    if 'directory' in kwargs:
        directory = kwargs.get('directory')
    if 'halo_location_x' in kwargs:
        halo_location_x = kwargs.get('halo_location_x')
    if 'halo_location_y' in kwargs:
        halo_location_y = kwargs.get('halo_location_y')

    z_range_of_boxes = np.linspace(z_start,z_end,nboxes)
#print(z_end)
#   print(z_start)
#   print(nboxes)
#   print(z_range_of_boxes)

    ####################################################
    # useful functions
    ####################################################

    def box_maker(name):       #reads in the boxes
        data = np.fromfile(directory + name ,dtype=np.float32)
        box = data.reshape((DIM,DIM,DIM))
        return box

    box_path = np.zeros((len(z_range_of_boxes)), dtype = 'object')
    box_path_redshifts = np.zeros((len(box_path)))
    for fn in os.listdir(directory):   #parse the boxes
        #print(fn)
        for z in range(len(z_range_of_boxes)):
            if marker in fn and str(z_range_of_boxes[z]) in fn:
                box_path[z] = fn
                index = box_path[z].find('_z0')
                start = index + len('_z0')
                box_path_redshifts[z] = float(box_path[z][start:start + 4])

    print(box_path_redshifts)
    print(box_path)

    #function to determine weighting of each redshift to boxes
    def find_sandwiched_bins(z_range, z):
        z_floor = np.min(z_range)
        z_ceil = z_range[1]
        binn = 1
        while(z_ceil <= np.max(z_range)):
            if ((z >= z_floor) and (z < z_ceil)):
                return (z_floor, z_ceil)
            z_floor = z_ceil
            if z_ceil == np.max(z_range):
                break
            z_ceil = z_range[binn+1]
            binn += 1
            #safety net
            if binn > 1000:
                break

    def comoving2pixel(DIM, Box_length, comoving_distance):
        return int(float(comoving_distance * DIM)/float(Box_length))

    def didweswitchbox(historyofzminus, z_minus, ctr):
        if z_minus > historyofzminus[ctr - 1 ]:
            return True

    ####################################################
    # initialize all relevant arrays
    ####################################################

    lightcone = np.zeros((N, DIM, DIM))
    lightcone_halo = np.zeros((N))
    z_range = np.linspace(z_start,z_end,N)

    z = z_range[0]
    ctr = 0
    comoving_distance_z0_zstart = cosmo.comoving_distance(z_range[0]).value
    prev_pix_loc = 0
    pixel_addition = 0
    pixel_origin = 0
    pixel_location_relative_to_origin = 0
    historyofzminus = []

    ####################################################
    # loop through redshifts
    ####################################################

    while(z < np.max(z_range)):
        z_sandwhich = find_sandwiched_bins(box_path_redshifts, z)
        z_minus = z_sandwhich[0]
        historyofzminus.append(z_minus)
        z_plus = z_sandwhich[1]
        xH_minus = box_maker(box_path[list(box_path_redshifts).index(z_minus)])
        xH_plus = box_maker(box_path[list(box_path_redshifts).index(z_plus)])
        
        comoving_distance_z = cosmo.comoving_distance(z).value
        comoving_distance_z0_to_z = comoving_distance_z  - comoving_distance_z0_zstart
        comoving_distance_from_last_switch = cosmo.comoving_distance(z_minus).value
        
        
        if ctr == 0:
            pixel_addition = comoving2pixel(DIM,Box_length, comoving_distance_z-comoving_distance_z0_zstart)
            prev_pix_loc = pixel_addition
            pixel_origin = 0
        else:
            if didweswitchbox(historyofzminus, z_minus, ctr):
                pixel_origin = prev_pix_loc
            pixel_location_relative_to_origin = comoving2pixel(DIM,Box_length, comoving_distance_z-comoving_distance_from_last_switch)
            pixel_addition = (pixel_location_relative_to_origin + pixel_origin)%DIM
            prev_pix_loc = pixel_addition
        
        #lightcone[ctr,:,:] =  (xH_plus[:,:,pixel_addition] - xH_minus[:,:,pixel_addition])*((z - z_minus)/(z_plus - z_minus)) + xH_minus[:,:,pixel_addition]
    
        lightcone_halo[ctr] =  (xH_plus[halo_location_x][halo_location_y][pixel_addition] - xH_minus[halo_location_x][halo_location_y][pixel_addition])*((z - z_minus)/(z_plus - z_minus)) + xH_minus[halo_location_x][halo_location_y][pixel_addition]

        ctr += 1
        z = z_range[ctr]
        #pl.savefig(str(ctr)+'.png')
        #safety net
        if ctr > N:
            break

    #return the lightcone history as an array across all redshifts

    return lightcone_halo

