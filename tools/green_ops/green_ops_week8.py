# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Reproduce frozen Week8 study in separate, exclusive output directories."""
from pathlib import Path
import sys
from green_ops_build_dataset import ArgumentParser
from ml_dataset import publish_files,load_dataset as load_original
from week8_dataset import materialize,load_dataset,frozen_models
from week8_workflow import ablation_files,calibration_inventory,evaluate
from uncertainty import calibrate
from explainability import explanation_from_bytes


def main(argv=None):
    parser=ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True)
    sub=commands.add_parser('materialize');sub.add_argument('--recipe',type=Path,required=True);sub.add_argument('--lineage',type=Path,required=True)
    sub.add_argument('--output-dir',type=Path,required=True)
    for name in ('ablations','calibrate','evaluate'):
        sub=commands.add_parser(name);sub.add_argument('--dataset',type=Path,required=True);sub.add_argument('--output-dir',type=Path,required=True)
        sub.add_argument('--models',type=Path,required=True);sub.add_argument('--original-recipe',type=Path,required=True)
        if name=='ablations':sub.add_argument('--original-dataset',type=Path,required=True)
        else:sub.add_argument('--ablations',type=Path,required=True)
        if name=='evaluate':sub.add_argument('--calibration',type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        output=args.output_dir.resolve()
        inputs=[v.resolve() for k,v in vars(args).items() if isinstance(v,Path) and k!='output_dir']
        if output.exists() or any(output==p or p in output.parents for p in inputs):raise ValueError('output must be fresh and outside inputs')
        if args.command=='materialize':materialize(args.recipe,args.lineage,output,progress=print)
        else:
            data=load_dataset(args.dataset,progress=print);original_recipe=args.original_recipe.read_bytes()
            models=frozen_models(args.models,original_recipe,data['recipe'])
            if args.command=='ablations':files=ablation_files(load_original(args.original_dataset),data,models)
            else:
                ablations=args.ablations.read_bytes();explanation_from_bytes(ablations,data,models,kind='ablations')
                if args.command=='calibrate':files=calibration_inventory(calibrate(data,models,original_recipe),data,ablations)
                else:files=evaluate(data,models,original_recipe,args.calibration,ablations)
            publish_files(output,files)
    except (OSError,UnicodeError,ValueError) as error:
        print(f'error: {error}',file=sys.stderr);return 1
    print(f'{args.command}: completed analytical_simulation study.');return 0


if __name__=='__main__':raise SystemExit(main())
