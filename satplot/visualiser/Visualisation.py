import numpy as np
import mpl_toolkits.mplot3d as mplot3d
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits.mplot3d import proj3d

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.patches import FancyArrowPatch


def plotScan(obj,bnds=[],step=1,block=False):
	'''

	'''
	
	fig = plt.figure()
	label_str='plot_scan'
	fig.set_label(label_str)
	ax = fig.gca(projection='3d')	

	if len(bnds)!=0:
		xmin,xmax=bnds[0]
		ymin,ymax=bnds[1]
	else:
		xmin,xmax=0,np.sqrt(len(obj))
		ymin,ymax=0,np.sqrt(len(obj))


	x=np.arange(xmin,xmax,step)
	y=np.arange(xmin,xmax,step)
	X,Y=np.meshgrid(x,y)

	surf=ax.plot_surface(X,Y,obj,cmap=cm.coolwarm,linewidth=0)

	
	plt.axis('square')
	
	ax.set_title('Parameter Scan')
	
	plt.show(block=block)
	#plt.show (block = False)



def drawNodeContour(node,type='edge'):
	'''
	Plots the line on the most recent figure

	Parameters
	----------
	line : (2,3) ndarray
		end points of ray
	'''
	ax=findAx('draw_nodes_numbered')
	if ax==-1:
		print("Figure not found")
		return -1

	C1=node.face_verts
	C2=node.constrict_verts
	l1=len(C1)
	C1=np.vstack([C1,C1[0,:]])
	C2=np.vstack([C2,C2[0,:]])

	edge_list=[]
	constrict_list=[]

	for ii in range(l1):
		if type=='edge':
			xs=[C1[ii,0],C1[ii+1,0]]
			ys=[C1[ii,1],C1[ii+1,1]]
			zs=[C1[ii,2],C1[ii+1,2]]
			edge_list.append(Arrow3D(xs,ys,zs,mutation_scale=10,lw=2,arrowstyle='-|>',color='k'))
			ax.add_artist(edge_list[ii])
		elif type=='constrict':
			xs=[C2[ii,0],C2[ii+1,0]]
			ys=[C2[ii,1],C2[ii+1,1]]
			zs=[C2[ii,2],C2[ii+1,2]]
			constrict_list.append(Arrow3D(xs,ys,zs,mutation_scale=10,lw=2,arrowstyle='-|>',color='r'))
			ax.add_artist(constrict_list[ii])
	


	# plt.axis('square')    
	
	# ax.set_zlim(-600,600)
	# ax.set_ylim(-600,600)
	# ax.set_xlim(-600,600)
	# ax.set_xlabel('x')
	# ax.set_ylabel('y')
	# ax.set_zlabel('z')
	
	plt.show(block=False)

def drawContour(poly,ax=None,**kwargs):
	'''
	Draws the edge contour of the supplied polygon on the most recent figure

	Parameters
	----------
	line : (2,3) ndarray
		end points of ray
	'''
	if ax==None:
		ax=find_ax('draw_nodes_numbered')
		if ax==-1:
			print("Figure not found")
			return -1
	else:
		ax=ax

	C1=poly
	l1=len(C1)
	C1=np.vstack([C1,C1[0,:]])

	edge_list=[]
	constrict_list=[]

	for ii in range(l1):
		xs=[C1[ii,0],C1[ii+1,0]]
		ys=[C1[ii,1],C1[ii+1,1]]
		zs=[C1[ii,2],C1[ii+1,2]]
		edge_list.append(Arrow3D(xs,ys,zs,mutation_scale=10,lw=2,arrowstyle='-|>',**kwargs))
		ax.add_artist(edge_list[ii])
	


	# plt.axis('square')    
	
	# ax.set_zlim(-600,600)
	# ax.set_ylim(-600,600)
	# ax.set_xlim(-600,600)
	# ax.set_xlabel('x')
	# ax.set_ylabel('y')
	# ax.set_zlabel('z')
	
	plt.show(block=False)

def draw_mesh(SC,node_num=-1,visibility=False,vis_mask=[],edge_alpha=1):
	'''
	Draws a node mesh on the applicable node, best executed with draw_nodes with exclude active
	Notes
	-----
		If 'visibility' colouring mode is used, a vis_mask, or list of vis_masks must be supplied, 
		otherwise an InputException is thrown

		Black mesh elements are blocked, white is visible


	Parameters
	----------
	sc : Spacecraft class

	node_num : int
		number of node to draw the mesh for

	visibility : bool
		Colour mesh using vis_mask

	vis_mask : [(n,n) bool ndarray,]
		list of masks to use for 'visibility' colouring mode
		will apply all the masks supplied

	edge_alpha : int [0,1]
		transparency of mesh edges
	'''
	ax=find_ax('')

	if isinstance(vis_mask,list):
		if len(vis_mask)!=0:
			for ii in range(len(vis_mask)):
				if ii==0:
					vis_sums=np.sum(vis_mask[ii],axis=0)
				else:
					vis_sums=vis_sums+np.sum(vis_mask[ii],axis=0)
	else:
		vis_sums=np.sum(vis_mask,axis=0)
	col_max=np.max(vis_sums)
	col_min=0
	col_norm=mpl.colors.Normalize(vmin=col_min,vmax=col_max)
	m=cm.ScalarMappable(norm=col_norm,cmap=cm.gray)

	if node_num==-1:
		for ii,node in enumerate(SC.node_list):
			points=node.mesh.points+node.norm_vec*0.01
			for jj,edge in enumerate(node.mesh.edges):
				ax.plot(points[edge[:],[0]],points[edge[:],[1]],points[edge[:],[2]],c='k',zorder=100)

	else:
		side=[]
		node=SC.node_list[node_num]
		points=node.mesh.points+node.norm_vec*0.1
		if not visibility:
			for jj,edge in enumerate(node.mesh.edges):
				ax.plot(points[edge[:],[0]],points[edge[:],[1]],points[edge[:],[2]],c='k',zorder=100)
		else:
			for kk,region in enumerate(node.mesh.elements):
				side.append(Poly3DCollection([node.mesh.points[region]]))
				side[kk]._facecolors3d=np.asarray([m.to_rgba(vis_sums[kk])])
				side[kk]._edgecolors3d=np.array([[0,0,0,edge_alpha]])
				side[kk].zorder=100
				ax.add_collection3d(side[kk])

	plt.axis('square')    
	
	ax.set_zlim(-600,600)
	ax.set_ylim(-600,600)
	ax.set_xlim(-600,600)
	ax.set_xlabel('x')
	ax.set_ylabel('y')
	ax.set_zlabel('z')

	plt.show(block=False)

def drawRay(line,c='k'):
	'''
	Plots the line on the most recent figure

	Parameters
	----------
	line : (2,3) ndarray
		end points of ray
	'''
	start=line[0,:]
	end=line[1,:]
	exis_fignums=plt.get_fignums()
	ax=plt.gca()

	line=np.asarray([start,end])
	print(line)
	ax.plot(line[:,0],line[:,1],line[:,2],c=c,zorder=100)
	plt.axis('square')    
	
	ax.set_zlim(-600,600)
	ax.set_ylim(-600,600)
	ax.set_xlim(-600,600)
	ax.set_xlabel('x')
	ax.set_ylabel('y')
	ax.set_zlabel('z')
	
	plt.show(block=False)



def drawShadowingRays(sc,inter_truth,new=False):
	'''
	Plots the nodes given in sc.node_list using inate colouring, and draws the rays
	used in the shadowing calculation. Rays indicating shadowing will be red, otherwise black.

	Notes
	-----
		Figure will have a label of the form 'draw_rays'

	Parameters
	----------
	sc : Spacecraft Class Object

	inter_truth : (n,n,x,4) bool ndarray
		truth table of whether the ray is intersected by another node
		depending on shadowing method used, x={0,4}

	new : bool
		Flag to draw in new window
	'''

	num_nodes=len(sc.node_list)

	ax=findAx('draw_rays')
	if ax==-1:
		print("Couldn't find figure with label draw_rays")

	if ax==-1 or new:
		fig = plt.figure()
		label_str='draw_rays'
		fig.set_label(label_str)
		ax = fig.gca(projection='3d')	
	
	
	lines_drawn=0
	if inter_truth.shape==(num_nodes,num_nodes,4,4):
		for ii in range(num_nodes):
			for jj in range(num_nodes):
				for vert_ii in range(4):
					for vert_jj in range(4):
							# if jj>ii:
								lines_drawn+=1
								line=np.asarray((sc.node_list[ii].face_verts[vert_ii,:],sc.node_list[jj].face_verts[vert_jj,:]))                          
								if inter_truth[ii,jj][vert_ii,vert_jj]==1:
									col='r'
								else:
									col='k'
								ax.plot(line[:,0],line[:,1],line[:,2],c=col)
	elif inter_truth.shape==(num_nodes,num_nodes,4):
		for ii in range(num_nodes):
			for jj in range(num_nodes):
				for vert_jj in range(4):
						# if jj>ii:
							lines_drawn+=1
							line=np.asarray((sc.node_list[ii].cen_vec,sc.node_list[jj].face_verts[vert_jj,:]))                          
							if inter_truth[ii,jj][vert_jj]==1:
								col='r'
							else:
								col='k'
							ax.plot(line[:,0],line[:,1],line[:,2],c=col)
	#Have to set axis to square before setting limits, otherwise limits are not respected
	print("rays_drawn:%d") %(lines_drawn)
	plt.axis('square')    
	
	ax.set_zlim(-600,600)
	ax.set_ylim(-600,600)
	ax.set_xlim(-600,600)
	ax.set_xlabel('x')
	ax.set_ylabel('y')
	ax.set_zlabel('z')
	ax.set_title('SkyHopper Face Shadowing Ray Tracing')

	
	plt.show(block=False)
	#plt.show (block = False)

def node_color(node_num):
	'''
	Returns a unique colour rgb triple

	Parameters
	----------
	node_num : int
	
	Returns
	-------
	(float,float,float,1)	

	'''		
	div=node_num/7+1
	r,g,b,a=_get_col_pat(node_num%7)
	return [r/float(div),g/float(div),b/float(div),1]

def _get_col_pat(x):
	return{
		0:[1,1,1,1],
		1:[1,0,0,1],
		2:[0,1,0,1],
		3:[0,0,1,1],
		4:[1,1,0,1],
		5:[1,0,1,1],
		6:[0,1,1,1],		
	}.get(x,-1)



def drawLinePlane(point,line,plane,new=False):
	fig = plt.figure()
	fig.set_label('test_intersection')
	ax = fig.gca(projection='3d')
	plt.cla()
	ax.plot(line[:,0],line[:,1],line[:,2])
	#Have to set axis to square before setting limits, otherwise limits are not respected
	
	side = Poly3DCollection([plane])
	side.set_color('c')
	ax.add_collection3d(side)
	ax.scatter(point[0],point[1],point[2],c='g')

	plt.axis('square')    
	
	# ax.set_zlim(-600,600)
	# ax.set_ylim(-600,600)
	# ax.set_xlim(-600,600)
	ax.set_zlim(-2,2)
	ax.set_ylim(-2,2)
	ax.set_xlim(-2,2)
	ax.set_xlabel('x')
	ax.set_ylabel('y')
	ax.set_zlabel('z')
		
	plt.show(block=False)
	# plt.show (block = False)

