import pandas as pd
import numpy as np
import streamlit as st 
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(layout="wide")

# Read data in
bbb = pd.read_csv('bbb_output.csv',low_memory=False)

# Create sidebar and list of batter with 1000+ IPL runs
batters = bbb.groupby('batter')["runsbatter"].sum().to_frame(name='Runs').reset_index()
batters = batters[batters["Runs"]>=1000]

batters = batters["batter"].tolist()
batters.sort()

st.sidebar.image('./img/Logo.png',use_column_width=True)
add_sidebar = st.sidebar.selectbox('IPL Batter',batters)

#Get Batter ball by ball (exclude wides and super over figs)
batter_stats = bbb[(bbb["batter"]==add_sidebar) & (bbb["wides"].isna()) & (bbb["innings"] < 3)]
batter_dismissals = bbb[(bbb["playerout"]==add_sidebar)&(bbb["innings"]<3)]

# Create career including dismissal info
career = batter_stats.groupby('match_id').agg(Runs=('runsbatter','sum'), 
                                                Balls=('batter','count'), 
                                                BPos=('bat_order','max'),
                                                Innings=('innings','max'),
                                                Result=('batter_match_result','max'))
# Because a player can be dismissed when they are not the striker dismissals need to be calculated seperately
career_dismissals = batter_dismissals.groupby('match_id').agg(Dismissals=('dismissal','sum'),
                                                                HowOut=('wicket','max'),
                                                                BowlStyle=('bowl_style','max'),
                                                                BowlingType=('bowl_type','max'))
# Add dismissal cols to career info
career['Dismissals'] = career_dismissals['Dismissals']
career['How Out']=career_dismissals['HowOut']
career['Bowling Style']=career_dismissals["BowlStyle"]
career['Bowling Type']=career_dismissals["BowlingType"]
career = career.fillna(0)
career['How Out'] = career['How Out'].replace(0,'Not Out')

# Create career groupby with phase and bowling style

#print(batter_stats)

batter_stats = batter_stats.replace('run out',None)
batter_stats = batter_stats.replace('retired hurt',None)
batter_stats = batter_stats.replace('retired out', None)
batter_stats = batter_stats.replace('obstructing the field',None)

career_phase_bowl_style_gb = batter_stats.groupby(['Phase','bowl_style']).agg(Runs=('runsbatter','sum'), 
                                                                            Balls=('batter','count'),
                                                                            Dismissals=('wicket','count')).reset_index()
career_phase_bowl_style_gb['Bowling Style'] = career_phase_bowl_style_gb.bowl_style

print(career_phase_bowl_style_gb)

bat_rpi = []
run_tot = 0
dismissal_tot = 0
for k,v in enumerate(career["Runs"]):
    run_tot += v
    if career["Dismissals"].iloc[[k]].tolist()[0] != 0:
        dismissal_tot += 1
    if dismissal_tot > 0:
        bat_rpi.append(round(run_tot/dismissal_tot,2))
    else:
        bat_rpi.append(run_tot)

career["Avg"] = bat_rpi
#st.write(career)
#print(career)

st.markdown(f"<h1 style='text-align: center;'>{add_sidebar} - IPL Career Batting Analysis (min 1000 runs)</h1>", unsafe_allow_html=True)

#col1 = st.columns(1)

#with col1:
#fig = px.line(career,y='Avg', width=800)
#fig.add_bar(career,y='Runs')
fig = go.Figure()

r = list(range(1,1+len(career["Runs"])))

#print(len(career["Runs"]))

fig.add_trace(go.Bar(x=r,y=career["Runs"],name='Runs'))
fig.add_trace(go.Line(x=r,y=career["Avg"],name='Career Avg'))
fig.update_layout(title=f'{add_sidebar} IPL Batting Career Overview'
                ,xaxis_title='Innings Number'
                ,yaxis_title='Runs'
                ,hovermode='x'
                ,template='none'
                ,legend=dict(orientation="h",yanchor="top",y=0.99,xanchor="left",x=0.01))
        
st.plotly_chart(fig, use_container_width=True)

# #Scoring Ranges Chart
# score_range = np.select(
#     [career["Runs"].between(0,0,inclusive = 'both'),
#     career["Runs"].between(1,9,inclusive = 'both'),
#     career["Runs"].between(10,19,inclusive = 'both'),
#     career["Runs"].between(20,49,inclusive = 'both'),
#     career["Runs"].between(50,89,inclusive = 'both'),
#     career["Runs"].between(90,99,inclusive = 'both'),
#     career["Runs"] >= 100
#     ]
#     ,
#     ['0','1-9','10-19','20-49','50-89','90-99','100+'],
#     default = -1
# )

# scores =[0,0,0,0,0,0,0]
# s_range_groups = ['0','1-9','10-19','20-49','50-89','90-99','100+']
# for v in score_range:
#     for i in range(len(s_range_groups)):
#         if v == s_range_groups[i]:
#             scores[i] += 1
#             continue
# scores = [100*(x/len(career)) for x in scores]
# with col2:
#     fig2 = px.bar(x=s_range_groups, y=scores, labels={'x':'Scoring Range','y':'%'}, color_discrete_sequence=['#1F77B4']*len(s_range_groups))
#     fig2.update_yaxes(range=[0,100])
#     fig2.update_layout(title=f'Career Scoring Ranges', template='none')
#     st.plotly_chart(fig2, use_container_width=True)

#Setup columns

col1, col2 = st.columns(2)

#Innings Avg SR Chart

inn = career.groupby('Innings').agg(Runs=('Runs','sum'), Balls=('Balls','sum'), Dismissals=('Dismissals','sum'))
inn['SR'] = 100*(inn['Runs']/inn['Balls'])
inn['Avg'] =  np.where(inn['Dismissals']>0,inn['Runs']/inn['Dismissals'],inn['Runs'])
if inn['SR'].max() > 190:
    plot_range = inn['SR'].max() + 10
else:
    plot_range = 200

avg_sr_colour_dict = {
    'Avg': '#1F77B4',
    'SR': '#FF7F0E'
}

with col1:
    fig3 = px.bar(inn,y=['Avg','SR'], barmode='group',color_discrete_map=avg_sr_colour_dict,labels={'value':'#','variable':'Legend'})
    fig3.update_layout(title=f'Avg and SR by Innings', template='none')
    fig3.update_yaxes(range=[0,plot_range])
    st.plotly_chart(fig3, use_container_width=True)

#BatPos Avg SR Chart
#print(career)
career['BPos'] = np.where(career['BPos']<3,'Open',career['BPos'])
inn = career.groupby('BPos').agg(Runs=('Runs','sum'), Balls=('Balls','sum'), Dismissals=('Dismissals','sum'))
inn['SR'] = 100*(inn['Runs']/inn['Balls'])
inn['Avg'] =  np.where(inn['Dismissals']>0,inn['Runs']/inn['Dismissals'],inn['Runs'])
if inn['SR'].max() > 190:
    plot_range = inn['SR'].max() + 10
else:
    plot_range = 200

with col2:
    fig4 = px.bar(inn,y=['Avg','SR'], barmode='group',color_discrete_map=avg_sr_colour_dict,labels={'value':'#','BPos':'Batting Position','variable':'Legend'}
                        ,category_orders={'BPos':['Open','3','4','5','6','7','8','9','10','11']})
    fig4.update_xaxes(type='category')
    fig4.update_yaxes(range=[0,plot_range])
    fig4.update_layout(title=f'Avg and SR by Batting Position',template='none')
    st.plotly_chart(fig4, use_container_width=True)

# #Innings Avg SR Chart

# inn = career.groupby('Result').agg(Runs=('Runs','sum'), Balls=('Balls','sum'), Dismissals=('Dismissals','sum'))
# inn['SR'] = 100*(inn['Runs']/inn['Balls'])
# inn['Avg'] =  np.where(inn['Dismissals']>0,inn['Runs']/inn['Dismissals'],inn['Runs'])
# if inn['SR'].max() > 190:
#     plot_range = inn['SR'].max() + 10
# else:
#     plot_range = 200

# with col3:
#     fig5 = px.bar(inn,y=['Avg','SR'], barmode='group',color_discrete_map=avg_sr_colour_dict,labels={'value':'#','variable':'Legend'})
#     fig5.update_xaxes(type='category',)
#     fig5.update_yaxes(range=[0,plot_range])
#     fig5.update_layout(title=f'Avg and SR by Result',template='none')
#     st.plotly_chart(fig5, use_container_width=True)

col11,col22 = st.columns([1,1])

# Bowling Style Avg SR Chart

inn = career_phase_bowl_style_gb.groupby('Bowling Style').agg(Runs=('Runs','sum'), Balls=('Balls','sum'), Dismissals=('Dismissals','sum'))
inn['SR'] = 100*(inn['Runs']/inn['Balls'])
inn['Avg'] =  np.where(inn['Dismissals']>0,inn['Runs']/inn['Dismissals'],inn['Runs'])
if inn['SR'].max() > 190:
    plot_range = inn['SR'].max() + 10
else:
    plot_range = 200

with col11:
    fig5 = px.bar(inn,y=['Avg','SR'], barmode='group',color_discrete_map=avg_sr_colour_dict,labels={'value':'#','variable':'Legend'})
    fig5.update_xaxes(type='category',)
    fig5.update_yaxes(range=[0,plot_range])
    fig5.update_layout(title=f'Avg and SR by Bowling Style',template='none')
    st.plotly_chart(fig5, use_container_width=True)

# Phase Avg SR Chart

inn = career_phase_bowl_style_gb.groupby('Phase').agg(Runs=('Runs','sum'), Balls=('Balls','sum'), Dismissals=('Dismissals','sum'))
inn['SR'] = 100*(inn['Runs']/inn['Balls'])
inn['Avg'] =  np.where(inn['Dismissals']>0,inn['Runs']/inn['Dismissals'],inn['Runs'])
if inn['SR'].max() > 190:
    plot_range = inn['SR'].max() + 10
else:
    plot_range = 200

with col22:
    fig55 = px.bar(inn,y=['Avg','SR'], barmode='group',color_discrete_map=avg_sr_colour_dict,labels={'value':'#','variable':'Legend'},
                            category_orders={'Phase':['pp','mdl','dth']})
    fig55.update_xaxes(type='category',)
    fig55.update_yaxes(range=[0,plot_range])
    fig55.update_layout(title=f'Avg and SR by Bowling Phase',template='none')
    st.plotly_chart(fig55, use_container_width=True)

col4,col5 = st.columns([1,1])
# Overall dismissal %age

# Dict for specific colours for each dismissal type

dismissal_type_dict = {
    'Not Out':'#FF9DA6',
    'caught': '#1F77B4',
    'bowled': '#EECA3B',
    'run out': '#54A24B',
    'caught and bowled': '#E45756',
    'lbw': '#B279A2',
    'stumped':'#9D755D',
    'hit wicket':'#BAB0AC',
    'obstructing the field':'#FECb52'
}

num_innings = len(career)
inn = career.groupby('How Out').agg(Num=('Runs','count')).reset_index()
inn['Num'] = round(100*(inn['Num']/num_innings),1)
inn['Batter'] = add_sidebar
#print(num_innings,inn)
fig6 = px.bar(inn,x='Batter',y='Num',color='How Out',color_discrete_map=dismissal_type_dict,labels={'Num':'%'})
fig6.update_layout(barmode='stack')
fig6.update_yaxes(range=[0,100])
fig6.update_layout(title=f'Career Dismissal Types',template='none')
with col4:
    st.plotly_chart(fig6, use_container_width=True)

# Dismissal %age by bowl type

inn=career[(career['Dismissals']>0) & (career['How Out']!='run out')]
#print(inn)
type_counts = inn.groupby('Bowling Style').agg(Num=('Runs','count'))
inn = inn.groupby(['Bowling Style','How Out']).agg(Num=('Runs','count'))
inn['Percentage'] = round(100*(inn['Num']/type_counts["Num"]),1)
inn = inn.reset_index()
#print(inn)
fig7 = px.bar(inn,x='Bowling Style',y='Percentage',color='How Out',color_discrete_map=dismissal_type_dict,labels={'Percentage':'%'})
#fig7.update_layout(showlegend=False)
fig7.update_yaxes(range=[0,100])
fig7.update_layout(title=f'Dismissal Type by Bowling Style',template='none')
with col5:  
    st.plotly_chart(fig7, use_container_width=True)

# # Dismissal %age by bowl style

# inn = career[career['Bowling Style'] != 0]
# inn = inn.groupby('Bowling Style').agg(Num=('Dismissals','sum'))
# inn['Percentage']=round(100*(inn["Num"]/num_innings),1)
# inn = inn.reset_index()
# print(inn)
# fig8 = px.bar(inn,x='Bowling Style',y='Percentage', color_discrete_sequence=['#1F77B4']*len(inn),labels={'Percentage':'%'})
# fig8.update_yaxes(range=[0,100])
# fig8.update_layout(title=f'Dismissals by Bowling Style',template='none')
# with col6:
#     st.plotly_chart(fig8, use_container_width=True)