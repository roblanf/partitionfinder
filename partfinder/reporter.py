#Copyright (C) 2011 Robert Lanfear and Brett Calcott
#
#This program is free software: you can redistribute it and/or modify it
#under the terms of the GNU General Public License as published by the
#Free Software Foundation, either version 3 of the License, or (at your
#option) any later version.
#
#This program is distributed in the hope that it will be useful, but
#WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#General Public License for more details. You should have received a copy
#of the GNU General Public License along with this program.  If not, see
#<http://www.gnu.org/licenses/>. PartitionFinder also includes the PhyML
#program and the PyParsing library both of which are protected by their
#own licenses and conditions, using PartitionFinder implies that you
#agree with those licences and conditions as well.

import logging
log = logging.getLogger("reporter")

import os

scheme_header_template = "%-15s: %s\n"
scheme_subset_template = "%-6s | %-10s | %-30s | %-30s | %-40s\n"
subset_template = "%-15s | %-15s | %-15s | %-15s | %-15s\n"

class TextReporter(object):
    def __init__(self, config):
        self.cfg = config

    def write_subset_summary(self, sub):
        pth = os.path.join(self.cfg.subsets_path, sub.name + '.txt')
        # Sort everything
        model_results = [(r.bic, r) for r in sub.results.values()]
        model_results.sort()
        f = open(pth, 'w')
        # TODO change back to full name...
        # f.write("Model selection results for subset: %s\n" % sub.full_name)
        f.write("Model selection results for subset: %s\n" % sub.name)
        f.write("Subset alignment stored here: %s\n" % sub.alignment_path)
        f.write("This subset contains the following data_blocks: %s\n" % sub)
        f.write("Models are organised according to their BIC scores\n\n")
        f.write(subset_template % ("Model", "lNL", "AIC", "AICc", "BIC"))
        for bic, r in model_results:
            f.write(subset_template % (r.model, r.lnl, r.aic, r.aicc, r.bic))

    # TODO. REMOVE 'write' from these. They could be output to a display
    def write_scheme_summary(self, result, output):
        self.write_scheme_header(result, output)
        sorted_subsets = [sub for sub in result.scheme]
        sorted_subsets.sort(key=lambda sub: min(sub.columns), reverse=False)
        self.write_subsets(result, output, sorted_subsets)
        self.write_raxml(result, output, sorted_subsets)

    def write_scheme_header(self, result, output):
        output.write(scheme_header_template % ("Scheme Name", result.scheme.name))
        output.write(scheme_header_template % ("Scheme lnL", result.lnl))
        output.write(scheme_header_template % ("Scheme AIC", result.aic))
        output.write(scheme_header_template % ("Scheme AICc", result.aicc))
        output.write(scheme_header_template % ("Scheme BIC", result.bic))
        output.write(scheme_header_template % ("Num params", result.sum_k))
        output.write(scheme_header_template % ("Num sites", result.nsites))
        output.write(scheme_header_template % ("Num subsets", result.nsubs))
        output.write("\n")

    def write_subsets(self, result, output, sorted_subsets):
        output.write(scheme_subset_template % (
            "Subset", "Best Model", "Subset Partitions", "Subset Sites",  "Alignment"))
        number = 1
        
        pf_scheme_description = [] #a way to print out the scheme in PF format
        
        for sub in sorted_subsets:
            desc = {}
            names= []
            for part in sub:
                names.append(part.name)
                for subpart in part.description: #loop through each sub-part of the partition
                    desc[subpart[0]] = subpart

            #pretty print the sites in the scheme
            desc_starts = desc.keys()
            desc_starts.sort()            
            parts = []
            for key in desc_starts:
                part = desc[key]
                if part[2]==1:
                    text = "%s-%s" %(part[0], part[1])
                else:
                    text = "%s-%s\\%s" % tuple(part)
                parts.append(text)
            parts = ', '.join(parts)
            	
            names.sort()
            names = ', '.join(names)

            pf_scheme_description.append("(%s)" %names)
			
            output.write(scheme_subset_template % (
                number, sub.best_model, names, parts, sub.alignment_path))
            number += 1

        pf_scheme_description = " ".join(pf_scheme_description)
        output.write("\n\nScheme Description in PartitionFinder format\n")
        output.write("Scheme_%s = %s;" % (result.scheme.name, pf_scheme_description))
            
    def write_raxml(self, result, output, sorted_subsets):
        """Print out partition definitions in RaxML-like format, might be
        useful to some people
        """
        output.write("\n\nRaxML-style partition definitions\n")
        number = 1
        for sub in sorted_subsets:
            desc = {}
            names= []
            for part in sub:
                names.append(part.name)
                for subpart in part.description: #loop through each sub-part of the partition
                    desc[subpart[0]] = subpart

            #pretty print the sites in the scheme
            desc_starts = desc.keys()
            desc_starts.sort()            
            parts = []
            for key in desc_starts:
                part = desc[key]
                if part[2]==1:
                    text = "%s-%s" %(part[0], part[1])
                else:
                    text = "%s-%s\\%s" % tuple(part)
                parts.append(text)
            parts = ', '.join(parts)
            line = "DNA, p%s = %s\n" %(number, parts)
            output.write(line)

            number += 1

    def write_best_schemes(self, best):
        best_schemes_pth = os.path.join(self.cfg.output_path, 'best_schemes.txt')
        output = open(best_schemes_pth, 'wb')

        for head, res in best:
            output.write(head)
            output.write("\n\n")
            self.write_scheme_summary(res, output)
            output.write("\n\n\n")

        log.info("Information on best schemes is here: %s", best_schemes_pth)

    def write_all_schemes(self, results):
        all_schemes_pth = os.path.join(self.cfg.output_path, 'all_schemes.txt')
        f = open(all_schemes_pth, 'wb')
        f.write("Name\tlnL\t#params\t#sites\t#subsets\tAIC\tAICc\tBIC\n")
        # This is in the default finalised order (should be BIC)
        for s in results.scheme_results:
            f.write("%s\t%.3f\t%d\t%d\t%d\t%.3f\t%.3f\t%.3f\n" % (
                s.scheme.name,s.lnl,s.sum_k,s.nsites,s.nsubs,s.aic,s.aicc,s.bic))
        log.info("Information on all schemes analysed is here: %s", all_schemes_pth)
