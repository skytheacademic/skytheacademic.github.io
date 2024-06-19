### www.skytheacademic.com plots ###
# Sky Kunkel #
# 6/19/2024 #

#### Set Libraries, read in data ####
library(tidyverse); library(ggstream); library(lubridate); library(sf); 
library(rstatix); library(ggpubr); library(ggExtra); library(ggridges)
library(viridis); library(hrbrthemes); library(tidyquant)

# set up environment
options(scipen = 999) # turn off scientific notation
setwd(dirname(rstudioapi::getActiveDocumentContext()$path)) # set to source file location
rm(list = ls()) # clear environment



##### Violence as a Condition #####

a = read.csv("../../car_wagner_analysis/data/Kunkel-Ellis-final.csv") %>%
  mutate(
    event_date = ymd(event_date),
    wagner = ifelse(t_ind == 1, "Wagner", "State Violence")
  )


## joyplot ##
a$act = NA
a$act[a$iv == 0 & a$t_ind == 1] = "Wagner, Pre-Ukraine"
a$act[a$iv == 1 & a$t_ind == 1] = "Wagner, Post-Ukraine"
a$act[a$iv == 0 & a$t_ind == 0] = "State, Pre-Ukraine"
a$act[a$iv == 1 & a$t_ind == 0] = "State, Post-Ukraine"

svg("./car.svg", width = 10, height = 7)
ggplot(a, aes(x = `fatalities`, y = `act`, fill = stat(x))) +
  geom_density_ridges_gradient(scale = 1.5, rel_min_height = 0.01, alpha = 0.5) +
  scale_fill_gradient(low = "#ff3b3b", high = "#000000", space = "Lab",
                      guide = "colourbar", aesthetics = "fill") +
  xlim(-1.75, 26) + 
  labs(title = 'Violence in the CAR, pre- and post-Ukraine', x = "Fatalities", y = "") +
  theme_ipsum() +
  annotate(geom="text", x=20.5, y=4.5, label= "bar(x)", color="black", parse=TRUE, size = 5) +
  annotate(geom="text", x=23.5, y=4.5, label= "= 5.89", color="black", size = 5) +
  annotate(geom="text", x=23.5, y=3.5, label="   9.07", color="black", size = 5) +
  annotate(geom="text", x=23.5, y=2.5, label="   2.42", color="black", size = 5) +
  annotate(geom="text", x=23.5, y=1.5, label="   1.74", color="black", size = 5) +
  theme(
    plot.title = element_text(family="Times", size = 20),
    legend.position = "none",
    panel.spacing = unit(0.1, "lines"),
    strip.text.x = element_text(size = 14),
    axis.title.x = element_text(size = 14, hjust = 0.4),
    axis.text.x = element_text(size = 16),
    axis.text.y = element_text(size = 16),
    plot.caption = element_text(size = 12)
  )
dev.off()

#### scatter plot of violence since 2021-11-01 #####
rm(list = ls())
a = read.csv("../../car_wagner_analysis/data/Kunkel-Ellis-final.csv") %>%
  mutate(event_date = ymd(event_date)) %>%
  mutate(event_date = floor_date(event_date, "week"),
         wagner = ifelse(t_ind == 1, "Wagner", "State"))
date = rep(ymd("2021-11-01"), nrow(a))
a$score = date - a$event_date
d = a %>%
  mutate(score = score*(-1)) %>%
  filter(score > -500) %>%
  group_by(score, wagner) %>%
  summarize(death = mean(death), fatalities = sum(fatalities)) %>%
  as.data.frame()

svg("./car_1.svg", width = 10, height = 7)
ggplot(d) + 
  geom_point(aes(x = score, y = fatalities, colour = wagner)) +
  geom_vline(xintercept = 0, linetype = "longdash", color = "black") +
  geom_ma(ma_fun = SMA, n = 14, aes(x = score, y = fatalities, 
                                    colour = wagner, linetype = "solid")) +
  xlab("Days Before and After Nov. 1, 2021") + ylab("Fatalities") +
  labs(colour = "Actor") + guides(linetype = "none") + ylim(0,120) +
  scale_color_manual(labels = c("State Forces", "Wagner"), values = c("#A52A2A", "#000000")) +
  theme_pubr() +
  theme(
    plot.title = element_text(size = 20),
    panel.spacing = unit(0.1, "lines"),
    strip.text.x = element_text(size = 14),
    axis.title.x = element_text(size = 14, hjust = 0.4),
    axis.text.x = element_text(size = 16),
    axis.text.y = element_text(size = 16),
    plot.caption = element_text(size = 12),
    legend.text = element_text(size = 12),
    legend.key.size = unit(1.5, "lines")
  )
dev.off()


###### Who Keeps the Peace ######
rm(list = ls())
a = readRDS("../../who_keeps/data/kunkel_which_pks.rds") %>% 
  as.data.frame()

df = a %>%
  group_by(prio.grid) %>%
  summarize(f_pko_deployed = sum(radpko_f_pko_deployed), m_pko_deployed = sum(radpko_m_pko_deployed), 
            violence = sum(ucdp_reb_vac_all, ucdp_gov_vac_all))

# change 0s to NA to make plot prettier
df$f_pko_deployed[df$f_pko_deployed == 0] <- NA
df$m_pko_deployed[df$m_pko_deployed == 0] <- NA
df$violence[df$violence == 0] <- NA

# restructure the data so grids can be duplicated and pko/violence is on the same scale 
# and named the same variable
df.pk_f = subset(df, f_pko_deployed > 0) %>%
  select(-c("violence", "m_pko_deployed")) %>%
  rename(count = f_pko_deployed)
df.pk_f$ct.type = "Women PKs Deployed"
df.pk_m = subset(df, m_pko_deployed > 0) %>%
  select(-c("violence", "f_pko_deployed")) %>%
  rename(count = m_pko_deployed)
df.pk_m$ct.type = "Men PKs Deployed"
df.vo = subset(df, violence > 0) %>%
  select(-c("m_pko_deployed", "f_pko_deployed")) %>%
  rename(count = violence)
df.vo$ct.type = "Violent Deaths"

# rejoin to same column
dd = rbind(df.pk_f, df.pk_m, df.vo)

rm(list = setdiff(ls(), c("dd", "df"))) 
gc()

### MERGE ACLED DATA WITH PRIO GRID IDS ###
prio_shp <- st_read(dsn = "../../who_keeps/data/prio", layer = "priogrid_cell", # get prio shapefiles
                    stringsAsFactors = F)
afr_shp <- st_read(dsn = "../../who_keeps/data/gadm/africa", layer = "afr_g2014_2013_0", # get Africa shapefiles
                   stringsAsFactors = F)

### save the CRS
proj_crs <- st_crs(prio_shp)
dd$gid = dd$prio.grid
dd$prio.grid = NULL
df$gid = df$prio.grid
df$prio.grid = NULL
# convert, get rid of useless data
df.prio = left_join(df, prio_shp, by = "gid") %>%
  select(-c(2:7))
df = left_join(df, prio_shp, by = "gid") %>%
  as.data.frame() %>%
  select(-c("geometry", "col", "row"))
dd_ac = left_join(dd, prio_shp, by = "gid") %>%
  as.data.frame() %>%
  select(-c("geometry", "col", "row"))
df_ac= df %>%
  drop_na(violence) # drop NAs
df_pk = df %>%
  drop_na(f_pko_deployed, m_pko_deployed)

# plot of variables as different colors and different shape


dsc.wom =
  ggplot(afr_shp) + geom_sf(aes(geometry = geometry), alpha = 0.3,fill = NA) + # e5695b
  geom_point(data = df, aes(x = xcoord, y = ycoord, size=f_pko_deployed, colour = "#9E314B"), alpha=0.5, shape = 19) +
  scale_fill_viridis_c(option="E") +
  scale_size(range = c(.1, 15), name="Count", labels = c("10,000", "20,000"), breaks = c(10000, 20000)) +
  theme_void()

dsc_wom = dsc.wom + 
  labs(colour = "Variable") + 
  scale_color_manual(labels = c("Women PKs Deployed"), values = c("#9E314B")) +
  theme(legend.background = element_rect(color = "black"), legend.position = c(0.25, 0.2),
        plot.margin = unit(c(0,0,0,0), "cm"), legend.margin=margin(c(2,2,2,2)), 
        legend.key.size = unit(2, 'cm'),
        legend.text = element_text(size = 14)
        ) + 
  guides(shape = guide_legend(order = 1),col = guide_legend(order = 2), legend.direction="vertical") +
  xlim(-14,37) + ylim(-12,21)

svg("./women_map.svg", width = 10, height = 7)
dsc_wom
dev.off()

dsc.men =
  ggplot(afr_shp) + geom_sf(aes(geometry = geometry), alpha = 0.3,fill = NA) +
  geom_point(data = df, aes(x = xcoord, y = ycoord, size=m_pko_deployed, colour = "#EB5307"), alpha=0.5, shape = 19) +
  scale_fill_viridis_c(option="E") +
  scale_size(range = c(.1, 24), name="Count", labels = c("250,000", "500,000"), breaks = c(250000, 500000)) +
  theme_void()

dsc_men = dsc.men + 
  labs(colour = "Variable") + 
  scale_color_manual(labels = c("Men PKs Deployed"), values = c("#EB5307")) +
  theme(legend.background = element_rect(color = "black"), legend.position = c(0.25, 0.2),
        plot.margin = unit(c(0,0,0,0), "cm"), legend.margin=margin(c(2,2,2,2)), 
        legend.key.size = unit(2, 'cm'),
        legend.text = element_text(size = 14)
  ) + 
  guides(shape = guide_legend(order = 1),col = guide_legend(order = 2), legend.direction="vertical") +
  xlim(-14,37) + ylim(-12,21)

svg("./men_map.svg", width = 10, height = 7)
dsc_men
dev.off()
