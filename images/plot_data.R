### www.skytheacademic.com plots ###
# Sky Kunkel #
# 6/19/2024 #

#### Set Libraries, read in data ####
library(tidyverse); library(ggstream); library(lubridate); library(sf); 
library(rstatix); library(ggpubr); library(ggExtra); library(ggridges)
library(viridis); library(hrbrthemes)

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
    axis.text = element_text(size = 16),
    axis.title.y = element_text(size = 16),
    plot.caption = element_text(size = 12)
  )
dev.off()

#### scatter plot of violence since 2021-11-01 #####
rm(list=ls())
a = read.csv("./data/Kunkel-Ellis-final.csv") %>%
  mutate(event_date = ymd(event_date)) %>%
  mutate(event_date = floor_date(event_date, "week"))
a$wagner = "State"
a$wagner[a$t_ind == 1] = "Wagner"
date = rep(ymd("2021-11-01"), nrow(a))
a$score = date - a$event_date
d = a %>%
  mutate(score = score*(-1)) %>%
  filter(score > -500) %>%
  group_by(score, wagner) %>%
  summarize(death = mean(death), fatalities = sum(fatalities)) %>%
  as.data.frame()

library(tidyquant)
death = 
  ggplot(d) + 
  geom_point(aes(x = score, y = fatalities, colour = wagner)) +
  geom_vline(xintercept = 0, linetype = "longdash", color = "black") +
  geom_ma(ma_fun = SMA, n = 14, aes(x = score, y = fatalities, 
                                    colour = wagner, linetype = "solid")) +
  xlab("Days Before and After Nov. 1, 2021") + ylab("Fatalities") +
  labs(colour = "Actor") + guides(linetype = "none") + ylim(0,120) +
  scale_color_manual(labels = c("State Forces", "Wagner"), values = c("#A52A2A", "#000000")) +
  theme_pubr()

# with marginal histogram
pdf("./results/death_scatter.pdf")
death
dev.off()